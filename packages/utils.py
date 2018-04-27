from collections import defaultdict
from itertools import chain
from operator import attrgetter, itemgetter
import re

from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.db.models import Count, Max, F
from django.db.models.query import QuerySet
from django.contrib.auth.models import User

from main.models import Package, PackageFile, Arch, Repo
from main.utils import (database_vendor,
        groupby_preserve_order, PackageStandin)
from .models import (PackageGroup, PackageRelation,
        License, Depend, Conflict, Provision, Replacement,
        SignoffSpecification, Signoff, fake_signoff_spec)


VERSION_RE = re.compile(r'^((\d+):)?(.+)-([^-]+)$')


def parse_version(version):
    match = VERSION_RE.match(version)
    if not match:
        return None, None, 0
    ver = match.group(3)
    rel = match.group(4)
    if match.group(2):
        epoch = int(match.group(2))
    else:
        epoch = 0
    return ver, rel, epoch


def get_group_info(include_arches=None):
    raw_groups = PackageGroup.objects.values_list(
            'name', 'pkg__arch__name').order_by('name').annotate(
            cnt=Count('pkg'), last_update=Max('pkg__last_update'))
    # now for post_processing. we need to separate things out and add
    # the count in for 'any' to all of the other architectures.
    group_mapping = {}
    for grp in raw_groups:
        arch_groups = group_mapping.setdefault(grp[1], {})
        arch_groups[grp[0]] = {'name': grp[0], 'arch': grp[1],
                'count': grp[2], 'last_update': grp[3]}

    # we want to promote the count of 'any' packages in groups to the
    # other architectures, and also add any 'any'-only groups
    if 'any' in group_mapping:
        any_groups = group_mapping['any']
        del group_mapping['any']
        for arch, arch_groups in group_mapping.items():
            for grp in any_groups.values():
                if grp['name'] in arch_groups:
                    found = arch_groups[grp['name']]
                    found['count'] += grp['count']
                    if grp['last_update'] > found['last_update']:
                        found['last_update'] = grp['last_update']
                else:
                    new_g = grp.copy()
                    # override the arch to not be 'any'
                    new_g['arch'] = arch
                    arch_groups[grp['name']] = new_g

    # now transform it back into a sorted list, including only the specified
    # architectures if we got a list
    groups = []
    for key, val in group_mapping.items():
        if not include_arches or key in include_arches:
            groups.extend(iter(val.values()))
    return sorted(groups, key=itemgetter('name', 'arch'))


def get_split_packages_info():
    '''Return info on split packages that do not have an actual package name
    matching the split pkgbase.'''
    pkgnames = Package.objects.values('pkgname')
    split_pkgs = Package.objects.exclude(pkgname=F('pkgbase')).exclude(
            pkgbase__in=pkgnames).values('pkgbase', 'repo', 'arch').annotate(
            last_update=Max('last_update')).distinct()
    all_arches = Arch.objects.in_bulk({s['arch'] for s in split_pkgs})
    all_repos = Repo.objects.in_bulk({s['repo'] for s in split_pkgs})
    for split in split_pkgs:
        split['arch'] = all_arches[split['arch']]
        split['repo'] = all_repos[split['repo']]
    return split_pkgs


class Difference(object):
    def __init__(self, pkgname, repo, pkg_a, pkg_b):
        self.pkgname = pkgname
        self.repo = repo
        self.pkg_a = pkg_a
        self.pkg_b = pkg_b

    def classes(self):
        '''A list of CSS classes that should be applied to this row in any
        generated HTML. Useful for sorting, filtering, etc. Contains whether
        this difference is in both architectures or the sole architecture it
        belongs to, as well as the repo name.'''
        css_classes = [self.repo.name.lower()]
        if self.pkg_a and self.pkg_b:
            css_classes.append('both')
        elif self.pkg_a:
            css_classes.append(self.pkg_a.arch.name)
        elif self.pkg_b:
            css_classes.append(self.pkg_b.arch.name)
        return ' '.join(css_classes)

    def __key(self):
        return (self.pkgname, hash(self.repo),
                hash(self.pkg_a), hash(self.pkg_b))

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())


def get_differences_info(arch_a, arch_b):
    # This is a monster. Join packages against itself, looking for packages in
    # our non-'any' architectures only, and not having a corresponding package
    # entry in the other table (or having one with a different pkgver). We will
    # then go and fetch all of these packages from the database and display
    # them later using normal ORM models.
    sql = """
SELECT p.id, q.id
    FROM packages p
    LEFT JOIN packages q
    ON (
        p.pkgname = q.pkgname
        AND p.repo_id = q.repo_id
        AND p.arch_id != q.arch_id
        AND p.id != q.id
    )
    WHERE p.arch_id IN (%s, %s)
    AND (
        q.id IS NULL
        OR p.pkgver != q.pkgver
        OR p.pkgrel != q.pkgrel
        OR p.epoch != q.epoch
    )
"""
    cursor = connection.cursor()
    cursor.execute(sql, [arch_a.id, arch_b.id])
    results = cursor.fetchall()
    # column A will always have a value, column B might be NULL
    to_fetch = {row[0] for row in results}
    # fetch all of the necessary packages
    pkgs = Package.objects.normal().in_bulk(to_fetch)
    # now build a set containing differences
    differences = set()
    for row in results:
        pkg_a = pkgs.get(row[0])
        pkg_b = pkgs.get(row[1])
        # We want arch_a to always appear first
        # pkg_a should never be None
        if pkg_a.arch == arch_a:
            item = Difference(pkg_a.pkgname, pkg_a.repo, pkg_a, pkg_b)
        else:
            # pkg_b can be None in this case, so be careful
            name = pkg_a.pkgname if pkg_a else pkg_b.pkgname
            repo = pkg_a.repo if pkg_a else pkg_b.repo
            item = Difference(name, repo, pkg_b, pkg_a)
        differences.add(item)

    # now sort our list by repository, package name
    key_func = attrgetter('repo.name', 'pkgname')
    differences = sorted(differences, key=key_func)
    return differences


def multilib_differences():
    # Query for checking multilib out of date-ness
    if database_vendor(Package) == 'sqlite':
        pkgname_sql = """
            CASE WHEN ml.pkgname LIKE %s
                THEN SUBSTR(ml.pkgname, 7)
            WHEN ml.pkgname LIKE %s
                THEN SUBSTR(ml.pkgname, 1, LENGTH(ml.pkgname) - 9)
            ELSE
                ml.pkgname
            END
        """
    else:
        pkgname_sql = """
            CASE WHEN ml.pkgname LIKE %s
                THEN SUBSTRING(ml.pkgname, 7)
            WHEN ml.pkgname LIKE %s
                THEN SUBSTRING(ml.pkgname FROM 1 FOR CHAR_LENGTH(ml.pkgname) - 9)
            ELSE
                ml.pkgname
            END
        """
    sql = """
SELECT ml.id, reg.id
    FROM packages ml
    JOIN packages reg
    ON (
        reg.pkgname = (""" + pkgname_sql + """)
        AND reg.pkgver != ml.pkgver
    )
    JOIN repos r ON reg.repo_id = r.id
    WHERE ml.repo_id = %s
    AND r.testing = %s
    AND r.staging = %s
    AND reg.arch_id = %s
    ORDER BY ml.last_update
    """
    multilib = Repo.objects.get(name__iexact='multilib')
    x86_64 = Arch.objects.get(name='x86_64')
    params = ['lib32-%', '%-multilib', multilib.id, False, False, x86_64.id]

    cursor = connection.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()

    # fetch all of the necessary packages
    to_fetch = set(chain.from_iterable(results))
    pkgs = Package.objects.normal().in_bulk(to_fetch)

    return [(pkgs[ml], pkgs[reg]) for ml, reg in results]


def get_wrong_permissions():
    sql = """
SELECT DISTINCT id
    FROM (
        SELECT pr.id, p.repo_id, pr.user_id
        FROM packages p
        JOIN packages_packagerelation pr ON p.pkgbase = pr.pkgbase
        WHERE pr.type = %s
    ) mp
    LEFT JOIN (
        SELECT user_id, repo_id FROM user_profiles_allowed_repos ar
        INNER JOIN user_profiles up ON ar.userprofile_id = up.id
    ) ur
    ON mp.user_id = ur.user_id AND mp.repo_id = ur.repo_id
    WHERE ur.user_id IS NULL;
"""
    cursor = connection.cursor()
    cursor.execute(sql, [PackageRelation.MAINTAINER])
    to_fetch = [row[0] for row in cursor.fetchall()]
    relations = PackageRelation.objects.select_related(
            'user', 'user__userprofile').filter(
            id__in=to_fetch)
    return relations


def attach_maintainers(packages):
    '''Given a queryset or something resembling it of package objects, find all
    the maintainers and attach them to the packages to prevent N+1 query
    cascading.'''
    if isinstance(packages, QuerySet):
        pkgbases = packages.values('pkgbase')
    else:
        packages = list(packages)
        pkgbases = {p.pkgbase for p in packages if p is not None}
    rels = PackageRelation.objects.filter(type=PackageRelation.MAINTAINER,
            pkgbase__in=pkgbases).values_list(
            'pkgbase', 'user_id').order_by().distinct()

    # get all the user objects we will need
    user_ids = {rel[1] for rel in rels}
    users = User.objects.in_bulk(user_ids)

    # now build a pkgbase -> [maintainers...] map
    maintainers = defaultdict(list)
    for rel in rels:
        maintainers[rel[0]].append(users[rel[1]])

    annotated = []
    # and finally, attach the maintainer lists on the original packages
    for package in packages:
        if package is None:
            continue
        package.maintainers = maintainers[package.pkgbase]
        annotated.append(package)

    return annotated


def approved_by_signoffs(signoffs, spec):
    if signoffs:
        good_signoffs = sum(1 for s in signoffs if not s.revoked)
        return good_signoffs >= spec.required
    return False


class PackageSignoffGroup(object):
    '''Encompasses all packages in testing with the same pkgbase.'''
    def __init__(self, packages):
        if len(packages) == 0:
            raise Exception
        self.packages = packages
        self.user = None
        self.target_repo = None
        self.signoffs = set()
        self.default_spec = True

        first = packages[0]
        self.pkgbase = first.pkgbase
        self.arch = first.arch
        self.repo = first.repo
        self.version = ''
        self.last_update = first.last_update
        self.packager = first.packager
        self.maintainers = first.maintainers
        self.specification = fake_signoff_spec(first.arch)

        version = first.full_version
        if all(version == pkg.full_version for pkg in packages):
            self.version = version

    @property
    def package(self):
        '''Try and return a relevant single package object representing this
        group. Start by seeing if there is only one package, then look for the
        matching package by name, finally falling back to a standin package
        object.'''
        if len(self.packages) == 1:
            return self.packages[0]

        same_pkgs = [p for p in self.packages if p.pkgname == p.pkgbase]
        if same_pkgs:
            return same_pkgs[0]

        return PackageStandin(self.packages[0])

    def find_signoffs(self, all_signoffs):
        '''Look through a list of Signoff objects for ones matching this
        particular group and store them on the object.'''
        for s in all_signoffs:
            if s.pkgbase != self.pkgbase:
                continue
            if self.version and not s.full_version == self.version:
                continue
            if s.arch_id == self.arch.id and s.repo_id == self.repo.id:
                self.signoffs.add(s)

    def find_specification(self, specifications):
        for spec in specifications:
            if spec.pkgbase != self.pkgbase:
                continue
            if self.version and not spec.full_version == self.version:
                continue
            if spec.arch_id == self.arch.id and spec.repo_id == self.repo.id:
                self.specification = spec
                self.default_spec = False
                return

    def approved(self):
        return approved_by_signoffs(self.signoffs, self.specification)

    @property
    def completed(self):
        return sum(1 for s in self.signoffs if not s.revoked)

    @property
    def required(self):
        return self.specification.required

    def user_signed_off(self, user=None):
        '''Did a given user signoff on this package? user can be passed as an
        argument, or attached to the group object itself so this can be called
        from a template.'''
        if user is None:
            user = self.user
        return user in (s.user for s in self.signoffs if not s.revoked)

    def __unicode__(self):
        return '%s-%s (%s): %d' % (
                self.pkgbase, self.version, self.arch, len(self.signoffs))


def signoffs_id_query(model, repos):
    sql = """
SELECT DISTINCT s.id
    FROM %s s
    JOIN packages p ON (
        s.pkgbase = p.pkgbase
        AND s.pkgver = p.pkgver
        AND s.pkgrel = p.pkgrel
        AND s.epoch = p.epoch
        AND s.arch_id = p.arch_id
        AND s.repo_id = p.repo_id
    )
    WHERE p.repo_id IN (%s)
    AND s.repo_id IN (%s)
    """
    cursor = connection.cursor()
    # query pre-process- fill in table name and placeholders for IN
    repo_sql = ','.join(['%s' for _ in repos])
    sql = sql % (model._meta.db_table, repo_sql, repo_sql)
    repo_ids = [r.pk for r in repos]
    # repo_ids are needed twice, so double the array
    cursor.execute(sql, repo_ids * 2)

    results = cursor.fetchall()
    return [row[0] for row in results]


def get_current_signoffs(repos):
    '''Returns a list of signoff objects for the given repos.'''
    to_fetch = signoffs_id_query(Signoff, repos)
    return list(Signoff.objects.select_related('user').in_bulk(to_fetch).values())


def get_current_specifications(repos):
    '''Returns a list of signoff specification objects for the given repos.'''
    to_fetch = signoffs_id_query(SignoffSpecification, repos)
    return list(SignoffSpecification.objects.select_related('arch').in_bulk(
            to_fetch).values())


def get_target_repo_map(repos):
    sql = """
SELECT DISTINCT p1.pkgbase, r.name
    FROM packages p1
    JOIN repos r ON p1.repo_id = r.id
    JOIN packages p2 ON p1.pkgbase = p2.pkgbase
    WHERE r.staging = %s
    AND r.testing = %s
    AND p2.repo_id IN (
    """
    sql += ','.join(['%s' for _ in repos])
    sql += ")"

    params = [False, False]
    params.extend(r.pk for r in repos)

    cursor = connection.cursor()
    cursor.execute(sql, params)
    return dict(cursor.fetchall())


def get_signoff_groups(repos=None, user=None):
    if repos is None:
        repos = Repo.objects.filter(testing=True)
    repo_ids = [r.pk for r in repos]

    test_pkgs = Package.objects.select_related(
            'arch', 'repo', 'packager').filter(repo__in=repo_ids)
    packages = test_pkgs.order_by('pkgname')
    packages = attach_maintainers(packages)

    # Filter by user if asked to do so
    if user is not None:
        packages = [p for p in packages if user == p.packager
                or user in p.maintainers]

    # Collect all pkgbase values in testing repos
    pkgtorepo = get_target_repo_map(repos)

    # Collect all possible signoffs and specifications for these packages
    signoffs = get_current_signoffs(repos)
    specs = get_current_specifications(repos)

    same_pkgbase_key = lambda x: (x.repo.name, x.arch.name, x.pkgbase)
    grouped = groupby_preserve_order(packages, same_pkgbase_key)
    signoff_groups = []
    for group in grouped:
        signoff_group = PackageSignoffGroup(group)
        signoff_group.target_repo = pkgtorepo.get(signoff_group.pkgbase,
                "Unknown")
        signoff_group.find_signoffs(signoffs)
        signoff_group.find_specification(specs)
        signoff_groups.append(signoff_group)

    return signoff_groups


DEPENDENCY_TYPES =  [('D', 'depends'), ('O', 'optdepends'),
                     ('M', 'makedepends'), ('C', 'checkdepends')]

class PackageJSONEncoder(DjangoJSONEncoder):
    pkg_attributes = ['pkgname', 'pkgbase', 'repo', 'arch', 'pkgver',
            'pkgrel', 'epoch', 'pkgdesc', 'url', 'filename', 'compressed_size',
            'installed_size', 'build_date', 'last_update', 'flag_date',
            'maintainers', 'packager']
    pkg_list_attributes = ['groups', 'licenses', 'conflicts',
            'provides', 'replaces']

    def default(self, obj):
        if hasattr(obj, '__iter__'):
            # mainly for queryset serialization
            return list(obj)
        if isinstance(obj, Package):
            data = {attr: getattr(obj, attr) for attr in self.pkg_attributes}
            for attr in self.pkg_list_attributes:
                data[attr] = getattr(obj, attr).all()
            all_deps = obj.depends.all()
            for (deptype, name) in DEPENDENCY_TYPES:
                data[name] = all_deps.filter(deptype=deptype)
            return data
        if isinstance(obj, PackageFile):
            filename = obj.filename or ''
            return obj.directory + filename
        if isinstance(obj, (Repo, Arch)):
            return obj.name.lower()
        if isinstance(obj, (PackageGroup, License)):
            return obj.name
        if isinstance(obj, (Depend, Conflict, Provision, Replacement)):
            return str(obj)
        elif isinstance(obj, User):
            return obj.username
        return super(PackageJSONEncoder, self).default(obj)

# vim: set ts=4 sw=4 et:

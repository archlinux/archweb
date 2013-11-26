from datetime import datetime
from itertools import groupby
from pgpdump import BinaryData

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from .fields import PositiveBigIntegerField
from .utils import set_created_field, DependStandin
from devel.models import DeveloperKey
from packages.alpm import AlpmAPI


class PackageManager(models.Manager):
    def flagged(self):
        """Used by dev dashboard."""
        return self.filter(flag_date__isnull=False)

    def normal(self):
        return self.select_related('arch', 'repo')

    def restricted(self, user=None):
        qs = self.normal()
        if user is not None and user.is_authenticated:
            return qs
        return qs.filter(repo__staging=False)


class Donor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    visible = models.BooleanField(default=True,
            help_text="Should we show this donor on the public page?")
    created = models.DateTimeField()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'donors'
        ordering = ('name',)
        get_latest_by = 'created'


class Arch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    agnostic = models.BooleanField(default=False,
            help_text="Is this architecture non-platform specific?")
    required_signoffs = models.PositiveIntegerField(default=2,
            help_text="Number of signoffs required for packages of this architecture")

    def __unicode__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    class Meta:
        db_table = 'arches'
        ordering = ('name',)
        verbose_name_plural = 'arches'


class Repo(models.Model):
    name = models.CharField(max_length=255, unique=True)
    testing = models.BooleanField(default=False,
            help_text="Is this repo meant for package testing?")
    staging = models.BooleanField(default=False,
            help_text="Is this repo meant for package staging?")
    bugs_project = models.SmallIntegerField(default=1,
            help_text="Flyspray project ID for this repository.")
    bugs_category = models.SmallIntegerField(default=2,
            help_text="Flyspray category ID for this repository.")
    svn_root = models.CharField(max_length=64,
            help_text="SVN root (e.g. path) for this repository.")

    def __unicode__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    class Meta:
        db_table = 'repos'
        ordering = ('name',)


class Package(models.Model):
    repo = models.ForeignKey(Repo, related_name="packages",
            on_delete=models.PROTECT)
    arch = models.ForeignKey(Arch, related_name="packages",
            on_delete=models.PROTECT)
    pkgname = models.CharField(max_length=255)
    pkgbase = models.CharField(max_length=255, db_index=True)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    epoch = models.PositiveIntegerField(default=0)
    pkgdesc = models.TextField('description', null=True)
    url = models.CharField('URL', max_length=255, null=True)
    filename = models.CharField(max_length=255)
    compressed_size = PositiveBigIntegerField()
    installed_size = PositiveBigIntegerField()
    build_date = models.DateTimeField(null=True)
    last_update = models.DateTimeField(db_index=True)
    files_last_update = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField()
    packager_str = models.CharField('packager string', max_length=255)
    packager = models.ForeignKey(User, null=True, blank=True,
            on_delete=models.SET_NULL)
    signature_bytes = models.BinaryField('PGP signature', null=True)
    flag_date = models.DateTimeField(null=True, blank=True)

    objects = PackageManager()

    class Meta:
        db_table = 'packages'
        ordering = ('pkgname',)
        get_latest_by = 'last_update'
        unique_together = (('pkgname', 'repo', 'arch'),)

    def __unicode__(self):
        return self.pkgname

    @property
    def full_version(self):
        if self.epoch > 0:
            return u'%d:%s-%s' % (self.epoch, self.pkgver, self.pkgrel)
        return u'%s-%s' % (self.pkgver, self.pkgrel)

    def get_absolute_url(self):
        return '/packages/%s/%s/%s/' % (self.repo.name.lower(),
                self.arch.name, self.pkgname)

    def get_full_url(self, proto='https'):
        '''get a URL suitable for things like email including the domain'''
        domain = Site.objects.get_current().domain
        return '%s://%s%s' % (proto, domain, self.get_absolute_url())

    @property
    def signature(self):
        if not self.signature_bytes:
            return None
        data = BinaryData(self.signature_bytes)
        packets = list(data.packets())
        return packets[0]

    @property
    def signer(self):
        sig = self.signature
        if sig and sig.key_id:
            try:
                matching_key = DeveloperKey.objects.select_related(
                        'owner').get(key=sig.key_id, owner_id__isnull=False)
                user = matching_key.owner
            except DeveloperKey.DoesNotExist:
                user = None
            return user
        return None

    _maintainers = None

    @property
    def maintainers(self):
        from packages.models import PackageRelation
        if self._maintainers is None:
            self._maintainers = User.objects.filter(
                    package_relations__pkgbase=self.pkgbase,
                    package_relations__type=PackageRelation.MAINTAINER)
        return self._maintainers

    @maintainers.setter
    def maintainers(self, maintainers):
        self._maintainers = maintainers

    _applicable_arches = None

    def applicable_arches(self):
        '''The list of (this arch) + (available agnostic arches).'''
        if self._applicable_arches is None:
            arches = set(Arch.objects.filter(agnostic=True))
            arches.add(self.arch)
            self._applicable_arches = list(arches)
        return self._applicable_arches

    def get_requiredby(self):
        """
        Returns a list of package objects. An attempt will be made to keep this
        list slim by including the corresponding package in the same testing
        category as this package if that check makes sense.
        """
        from packages.models import Depend
        sorttype = '''(CASE deptype
        WHEN 'D' THEN 0
        WHEN 'O' THEN 1
        WHEN 'M' THEN 2
        WHEN 'C' THEN 3
        ELSE 1000 END)'''
        name_clause = '''packages_depend.name IN (
        SELECT %s UNION ALL
        SELECT z.name FROM packages_provision z WHERE z.pkg_id = %s
        )'''
        requiredby = Depend.objects.select_related('pkg',
                'pkg__arch', 'pkg__repo').extra(
                select={'sorttype': sorttype},
                where=[name_clause], params=[self.pkgname, self.id]).order_by(
                'sorttype', 'pkg__pkgname',
                'pkg__arch__name', 'pkg__repo__name')
        if not self.arch.agnostic:
            # make sure we match architectures if possible
            requiredby = requiredby.filter(
                    pkg__arch__in=self.applicable_arches())

        # if we can use ALPM, ensure our returned Depend objects abide by the
        # version comparison operators they may specify
        alpm = AlpmAPI()
        if alpm.available:
            provides = self.provides.all()
            new_rqd = []
            for dep in requiredby:
                if not dep.comparison or not dep.version:
                    # no comparisson/version, so always let it through
                    new_rqd.append(dep)
                elif self.pkgname == dep.name:
                    # depends on this package, so check it directly
                    if alpm.compare_versions(self.full_version,
                            dep.comparison, dep.version):
                        new_rqd.append(dep)
                else:
                    # it must be a provision of ours at this point
                    for provide in (p for p in provides if p.name == dep.name):
                        if alpm.compare_versions(provide.version,
                                dep.comparison, dep.version):
                            new_rqd.append(dep)
                            break
            requiredby = new_rqd

        # sort out duplicate packages; this happens if something has a double
        # versioned depend such as a kernel module
        requiredby = [list(vals)[0] for _, vals in
                groupby(requiredby, lambda x: x.pkg.id)]
        if len(requiredby) == 0:
            return requiredby

        # do we have duplicate pkgbase values for non-primary depends?
        # if so, filter it down to base packages only
        def grouper(depend):
            p = depend.pkg
            return (depend.deptype, p.pkgbase, p.repo.testing, p.repo.staging)

        filtered = []
        for (typ, pkgbase, _, _), dep_pkgs in groupby(requiredby, grouper):
            dep_pkgs = list(dep_pkgs)
            if typ == 'D' or len(dep_pkgs) == 1:
                filtered.extend(dep_pkgs)
            else:
                filtered.append(DependStandin(dep_pkgs))

        # find another package by this name in a different testing or staging
        # repo; if we can't, we can short-circuit some checks
        repo_q = (Q(repo__testing=(not self.repo.testing)) |
                Q(repo__staging=(not self.repo.staging)))
        if not Package.objects.filter(
                repo_q, pkgname=self.pkgname, arch=self.arch
                ).exclude(id=self.id).exists():
            # there isn't one? short circuit, all required by entries are fine
            return filtered

        trimmed = []
        # for each unique package name, try to screen our package list down to
        # those packages in the same testing and staging category (yes or no)
        # iff there is a package in the same testing and staging category.
        for _, dep_pkgs in groupby(filtered, lambda x: x.pkg.pkgname):
            dep_pkgs = list(dep_pkgs)
            dep = dep_pkgs[0]
            if len(dep_pkgs) > 1:
                dep_pkgs = [d for d in dep_pkgs
                        if d.pkg.repo.testing == self.repo.testing and
                        d.pkg.repo.staging == self.repo.staging]
                if len(dep_pkgs) > 0:
                    dep = dep_pkgs[0]
            trimmed.append(dep)

        return trimmed

    def get_depends(self):
        """
        Returns a list of dicts. Each dict contains ('dep', 'pkg', and
        'providers'). If it represents a found package both vars will be
        available; else pkg will be None if it is a 'virtual' dependency.
        If pkg is None and providers are known, they will be available in
        providers.
        Packages will match the testing status of this package if possible.
        """
        deps = []
        # TODO: we can use list comprehension and an 'in' query to make this
        # more effective
        for dep in self.depends.all():
            pkg = dep.get_best_satisfier()
            providers = None
            if not pkg:
                providers = dep.get_providers()
            deps.append({'dep': dep, 'pkg': pkg, 'providers': providers})
        # sort the list; deptype sorting makes this tricker than expected
        sort_order = {'D': 0, 'O': 1, 'M': 2, 'C': 3}

        def sort_key(val):
            dep = val['dep']
            return (sort_order.get(dep.deptype, 1000), dep.name)
        return sorted(deps, key=sort_key)

    def reverse_conflicts(self):
        """
        Returns a list of packages with conflicts against this package.
        """
        pkgs = Package.objects.normal().filter(conflicts__name=self.pkgname)
        if not self.arch.agnostic:
            # make sure we match architectures if possible
            pkgs = pkgs.filter(arch__in=self.applicable_arches())

        alpm = AlpmAPI()
        if not alpm.available:
            return pkgs

        # If we can use ALPM, we can filter out items that don't actually
        # conflict due to the version specification.
        pkgs = pkgs.prefetch_related('conflicts')
        new_pkgs = []
        for package in pkgs:
            for conflict in package.conflicts.all():
                if conflict.name != self.pkgname:
                    continue
                if not conflict.comparison or not conflict.version \
                        or alpm.compare_versions(self.full_version,
                        conflict.comparison, conflict.version):
                    new_pkgs.append(package)
        return new_pkgs

    def base_package(self):
        """
        Locate the base package for this package. It may be this very package,
        or if it was built in a way that the base package isn't real, will
        return None.
        """
        try:
            # start by looking for something in this repo
            return Package.objects.normal().get(arch=self.arch,
                    repo=self.repo, pkgname=self.pkgbase)
        except Package.DoesNotExist:
            # this package might be split across repos? find one
            # that matches the correct [testing] repo flag
            pkglist = Package.objects.normal().filter(arch=self.arch,
                    repo__testing=self.repo.testing,
                    repo__staging=self.repo.staging, pkgname=self.pkgbase)
            if len(pkglist) > 0:
                return pkglist[0]
            return None

    def split_packages(self):
        """
        Return all packages that were built with this one (e.g. share a pkgbase
        value). The package this method is called on will never be in the list,
        and we will never return a package that does not have the same
        repo.testing and repo.staging flags. For any non-split packages, the
        return value will be an empty list.
        """
        return Package.objects.normal().filter(
                arch__in=self.applicable_arches(),
                repo__testing=self.repo.testing,
                repo__staging=self.repo.staging,
                pkgbase=self.pkgbase).exclude(id=self.id)

    def flag_request(self):
        if self.flag_date is None:
            return None
        from packages.models import FlagRequest
        try:
            # Note that we don't match on pkgrel here; this is because a pkgrel
            # bump does not unflag a package so we can still show the same flag
            # request from a different pkgrel.
            request = FlagRequest.objects.filter(pkgbase=self.pkgbase,
                    repo=self.repo, pkgver=self.pkgver,
                    epoch=self.epoch, is_spam=False).latest()
            return request
        except FlagRequest.DoesNotExist:
            return None

    def is_same_version(self, other):
        'is this package similar, name and version-wise, to another'
        return self.pkgname == other.pkgname \
                and self.pkgver == other.pkgver \
                and self.pkgrel == other.pkgrel \
                and self.epoch == other.epoch

    def in_testing(self):
        '''attempt to locate this package in a testing repo; if we are in
        a testing repo we will always return None.'''
        if self.repo.testing:
            return None
        try:
            return Package.objects.normal().get(repo__testing=True,
                    pkgname=self.pkgname, arch=self.arch)
        except Package.DoesNotExist:
            return None

    def in_staging(self):
        '''attempt to locate this package in a staging repo; if we are in
        a staging repo we will always return None.'''
        if self.repo.staging:
            return None
        try:
            return Package.objects.normal().get(repo__staging=True,
                    pkgname=self.pkgname, arch=self.arch)
        except Package.DoesNotExist:
            return None

    def elsewhere(self):
        '''attempt to locate this package anywhere else, regardless of
        architecture or repository. Excludes this package from the list.'''
        names = [self.pkgname]
        if self.pkgname.startswith(u'lib32-'):
            names.append(self.pkgname[6:])
        elif self.pkgname.endswith(u'-multilib'):
            names.append(self.pkgname[:-9])
        else:
            names.append(u'lib32-' + self.pkgname)
            names.append(self.pkgname + u'-multilib')
        return Package.objects.normal().filter(
                pkgname__in=names).exclude(id=self.id).order_by(
                'arch__name', 'repo__name')


class PackageFile(models.Model):
    pkg = models.ForeignKey(Package)
    is_directory = models.BooleanField(default=False)
    directory = models.CharField(max_length=255)
    filename = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return "%s%s" % (self.directory, self.filename or '')

    class Meta:
        db_table = 'package_files'


# connect signals needed to keep cache in line with reality
from main.utils import refresh_latest
from django.db.models.signals import pre_save, post_save

post_save.connect(refresh_latest, sender=Package,
        dispatch_uid="main.models")
# note: reporead sets the 'created' field on Package objects, so no signal
# listener is set up here to do so
pre_save.connect(set_created_field, sender=Donor,
        dispatch_uid="main.models")

# vim: set ts=4 sw=4 et:

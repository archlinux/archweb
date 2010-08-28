from django.db import connection
from django.db.models import Count, Max

from operator import itemgetter

from main.models import Package
from main.utils import cache_function
from .models import PackageGroup

@cache_function(300)
def get_group_info():
    raw_groups = PackageGroup.objects.values_list(
            'name', 'pkg__arch__name').order_by('name').annotate(
             cnt=Count('pkg'), last_update=Max('pkg__last_update'))
    # now for post_processing. we need to seperate things out and add
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
        for arch, arch_groups in group_mapping.iteritems():
            for grp in any_groups.itervalues():
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

    # now transform it back into a sorted list
    groups = []
    for val in group_mapping.itervalues():
        groups.extend(val.itervalues())
    return sorted(groups, key=itemgetter('name', 'arch'))

@cache_function(300)
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
        OR
        p.pkgver != q.pkgver
        OR
        p.pkgrel != q.pkgrel
    )
"""
    cursor = connection.cursor()
    cursor.execute(sql, [arch_a.id, arch_b.id])
    results = cursor.fetchall()
    to_fetch = []
    for row in results:
        # column A will always have a value, column B might be NULL
        to_fetch.append(row[0])
    # fetch all of the necessary packages
    pkgs = Package.objects.in_bulk(to_fetch)
    # now build a list of tuples containing differences
    differences = []
    for row in results:
        pkg_a = pkgs.get(row[0])
        pkg_b = pkgs.get(row[1])
        # We want arch_a to always appear first
        # pkg_a should never be None
        if pkg_a.arch == arch_a:
            item = (pkg_a.pkgname, pkg_a.repo, pkg_a, pkg_b)
        else:
            # pkg_b can be None in this case, so be careful
            name = pkg_a.pkgname if pkg_a else pkg_b.pkgname
            repo = pkg_a.repo if pkg_a else pkg_b.repo
            item = (name, repo, pkg_b, pkg_a)
        if item not in differences:
            differences.append(item)

    # now sort our list by repository, package name
    differences.sort(key=lambda a: (a[1].name, a[0]))
    return differences

# vim: set ts=4 sw=4 et:

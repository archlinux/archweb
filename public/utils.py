from collections import defaultdict
from operator import attrgetter

from main.models import Arch, Repo, Package
from main.utils import groupby_preserve_order, PackageStandin

class RecentUpdate(object):
    def __init__(self, packages):
        if len(packages) == 0:
            raise Exception
        first = packages[0]
        self.pkgbase = first.pkgbase
        self.repo = first.repo
        self.version = ''
        self.classes = set()

        self.classes.add(self.repo.name.lower())
        if self.repo.testing:
            self.classes.add('testing')
        if self.repo.staging:
            self.classes.add('staging')

        packages = sorted(packages, key=attrgetter('arch', 'pkgname'))
        # split the packages into two lists. we need to prefer packages
        # matching pkgbase as our primary, and group everything else in other.
        self.packages = [pkg for pkg in packages if pkg.pkgname == pkg.pkgbase]
        self.others = [pkg for pkg in packages if pkg.pkgname != pkg.pkgbase]

        if self.packages:
            version = self.packages[0].full_version
            if all(version == pkg.full_version for pkg in self.packages):
                self.version = version
        elif self.others:
            version = self.others[0].full_version
            if all(version == pkg.full_version for pkg in self.others):
                self.version = version

    def package_links(self):
        '''Returns either actual packages or package-standins for virtual
        pkgbase packages.'''
        if self.packages:
            # we have real packages- just yield each in sequence
            for package in self.packages:
                yield package
        else:
            # fake out the template- this is slightly hacky but yields one
            # 'package-like' object per arch which is what the normal loop does
            by_arch = defaultdict(list)
            for package in self.others:
                by_arch[package.arch].append(package)
            for _, packages in list(by_arch.items()):
                if len(packages) == 1:
                    yield packages[0]
                else:
                    yield PackageStandin(packages[0])

    def __unicode__(self):
        return "RecentUpdate '%s %s' <%d packages>" % (
                self.pkgbase, self.version, len(self.packages))

def get_recent_updates(number=15, testing=True, staging=False):
    repos = Repo.objects.all()
    if not testing:
        repos = repos.exclude(testing=True)
    if not staging:
        repos = repos.exclude(staging=True)

    # This is a bit of magic. We are going to show 15 on the front page, but we
    # want to try and eliminate cross-architecture wasted space. Pull enough
    # packages that we can later do some screening and trim out the fat.
    pkgs = []
    # grab a few extra so we can hopefully catch everything we need
    fetch = number * 6
    for arch in Arch.objects.all():
        pkgs += list(Package.objects.normal().filter(
            arch=arch, repo__in=repos).order_by('-last_update')[:fetch])
    pkgs.sort(key=attrgetter('last_update'), reverse=True)

    same_pkgbase_key = lambda x: (x.repo.name, x.pkgbase)
    grouped = groupby_preserve_order(pkgs, same_pkgbase_key)

    updates = []
    for group in grouped:
        update = RecentUpdate(group)
        updates.append(update)

    return updates[:number]

# vim: set ts=4 sw=4 et:

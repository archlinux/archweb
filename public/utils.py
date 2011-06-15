from operator import attrgetter

from main.models import Arch, Package, Repo
from main.utils import cache_function

class RecentUpdate(object):
    def __init__(self, packages):
        if len(packages) == 0:
            raise Exception
        first = packages[0]
        self.pkgbase = first.pkgbase
        self.repo = first.repo
        self.version = ''

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
            # time to fake out the template, this is a tad dirty
            arches = set(pkg.arch for pkg in self.others)
            for arch in arches:
                url = '/packages/%s/%s/%s/' % (
                        self.repo.name.lower(), arch.name, self.pkgbase)
                package_stub = {
                    'pkgname': self.pkgbase,
                    'arch': arch,
                    'repo': self.repo,
                    'get_absolute_url': url
                }
                yield package_stub

@cache_function(300)
def get_recent_updates(number=15):
    # This is a bit of magic. We are going to show 15 on the front page, but we
    # want to try and eliminate cross-architecture wasted space. Pull enough
    # packages that we can later do some screening and trim out the fat.
    pkgs = []
    # grab a few extra so we can hopefully catch everything we need
    fetch = number * 6
    for arch in Arch.objects.all():
        pkgs += list(Package.objects.normal().filter(
            arch=arch).order_by('-last_update')[:fetch])
    pkgs.sort(key=attrgetter('last_update'))

    updates = []
    while len(pkgs) > 0:
        pkg = pkgs.pop()

        in_group = lambda x: pkg.repo == x.repo and pkg.pkgbase == x.pkgbase
        samepkgs = [other for other in pkgs if in_group(other)]
        samepkgs.append(pkg)

        # now remove all the packages we just pulled out
        pkgs = [other for other in pkgs if other not in samepkgs]

        update = RecentUpdate(samepkgs)
        updates.append(update)

    return updates[:number]

# vim: set ts=4 sw=4 et:

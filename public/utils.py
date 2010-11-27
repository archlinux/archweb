from operator import attrgetter

from main.models import Arch, Package
from main.utils import cache_function

@cache_function(300)
def get_recent_updates():
    # This is a bit of magic. We are going to show 15 on the front page, but we
    # want to try and eliminate cross-architecture wasted space. Pull enough
    # packages that we can later do some screening and trim out the fat.
    pkgs = []
    for arch in Arch.objects.all():
        # grab a few extra so we can hopefully catch everything we need
        pkgs += list(Package.objects.select_related(
            'arch', 'repo').filter(arch=arch).order_by('-last_update')[:50])
    pkgs.sort(key=attrgetter('last_update'))
    updates = []
    ctr = 0
    while ctr < 15 and len(pkgs) > 0:
        # not particularly happy with this logic, but it works.
        p = pkgs.pop()
        is_same = lambda q: p.is_same_version(q) and p.repo == q.repo
        samepkgs = filter(is_same, pkgs)
        samepkgs.append(p)
        samepkgs.sort(key=attrgetter('arch'))
        updates.append(samepkgs)
        for q in samepkgs:
            if p != q: pkgs.remove(q)
        ctr += 1
    return updates

# vim: set ts=4 sw=4 et:

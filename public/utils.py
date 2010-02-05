from archweb.main.models import Arch, Repo, Package

def get_recent_updates():
    # This is a bit of magic. We are going to show 15 on the front page, but we
    # want to try and eliminate cross-architecture wasted space. Pull enough
    # packages that we can later do some screening and trim out the fat.
    pkgs = []
    for a in Arch.objects.all():
        # grab a few extra so we can hopefully catch everything we need
        pkgs += list(Package.objects.select_related('arch', 'repo').filter(arch=a).order_by('-last_update')[:50])
    pkgs.sort(reverse=True, key=lambda q: q.last_update)
    for p in pkgs:
        samepkgs = filter(lambda q: p.is_same_version(q), pkgs)
        p.allarches = '/'.join(sorted([q.arch.name for q in samepkgs]))
        for q in samepkgs:
            if p != q: pkgs.remove(q)
    return pkgs[:15]

# vim: set ts=4 sw=4 et:

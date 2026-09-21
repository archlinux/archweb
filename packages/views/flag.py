
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect

from main.models import Package


@permission_required('main.change_package')
def unflag(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
                            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    pkg.flag_date = None
    pkg.save()
    return redirect(pkg)


@permission_required('main.change_package')
def unflag_all(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
                            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    # find all packages from (hopefully) the same PKGBUILD
    pkgs = Package.objects.filter(pkgbase=pkg.pkgbase,
                                  repo__testing=pkg.repo.testing, repo__staging=pkg.repo.staging)
    pkgs.update(flag_date=None)
    return redirect(pkg)

# vim: set ts=4 sw=4 et:

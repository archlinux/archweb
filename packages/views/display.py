import datetime
import json
from urllib.parse import urlencode

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from main.models import Package, PackageFile, Arch, Repo
from main.utils import empty_response
from mirrors.utils import get_mirror_url_for_download
from ..models import Update
from ..utils import get_group_info, PackageJSONEncoder


def arch_plus_agnostic(arch):
    arches = [ arch ]
    arches.extend(Arch.objects.filter(agnostic=True).order_by())
    return arches


def split_package_details(request, name, repo, arch):
    '''Check if we have a split package (e.g. pkgbase) value matching this
    name. If so, we can show a listing page for the entire set of packages.'''
    arches = arch_plus_agnostic(arch)
    pkgs = Package.objects.normal().filter(pkgbase=name,
            repo__testing=repo.testing, repo__staging=repo.staging,
            arch__in=arches).order_by('pkgname')
    if len(pkgs) == 0:
        return None
    # we have packages, but ensure at least one is in the given repo
    if not any(True for pkg in pkgs if pkg.repo == repo):
        return None
    context = {
        'list_title': 'Split Package Details',
        'name': name,
        'arch': arch,
        'packages': pkgs,
    }
    return render(request, 'packages/packages_list.html', context)


CUTOFF = datetime.timedelta(days=60)


def recently_removed_package(request, name, repo, arch, cutoff=CUTOFF):
    '''Check our packages update table to see if this package has existed in
    this repo before. If so, we can show a 410 Gone page and point the
    requester in the right direction.'''
    arches = arch_plus_agnostic(arch)
    match = Update.objects.select_related('arch', 'repo').filter(
            pkgname=name, repo=repo, arch__in=arches)
    if cutoff is not None:
        when = now() - cutoff
        match = match.filter(created__gte=when)
    try:
        update = match.latest()
        elsewhere = update.elsewhere()
        if len(elsewhere) == 0:
            elsewhere = update.replacements()
        if len(elsewhere) == 1:
            return redirect(elsewhere[0])
        context = {
            'update': update,
            'elsewhere': elsewhere,
            'name': name,
            'version': update.old_version,
            'arch': arch,
            'repo': repo,
        }
        return render(request, 'packages/removed.html', context, status=410)
    except Update.DoesNotExist:
        return None


def replaced_package(request, name, repo, arch):
    '''Check our package replacements to see if this is a package we used to
    have but no longer do.'''
    match = Package.objects.filter(replaces__name=name, repo=repo, arch=arch)
    if len(match) == 1:
        return redirect(match[0], permanent=True)
    elif len(match) > 1:
        context = {
            'elsewhere': match,
            'name': name,
            'version': '',
            'arch': arch,
            'repo': repo,
        }
        return render(request, 'packages/removed.html', context, status=410)
    return None


def redirect_agnostic(request, name, repo, arch):
    '''For arch='any' packages, we can issue a redirect to them if we have a
    single non-ambiguous option by changing the arch to match any arch-agnostic
    package.'''
    if not arch.agnostic:
        # limit to 2 results, we only need to know whether there is anything
        # except only one matching result
        pkgs = Package.objects.select_related(
            'arch', 'repo', 'packager').filter(pkgname=name,
                    repo=repo, arch__agnostic=True)[:2]
        if len(pkgs) == 1:
            return redirect(pkgs[0], permanent=True)
    return None


def redirect_to_search(request, name, repo, arch):
    if request.GET.get('q'):
        name = request.GET.get('q')
    pkg_data = [
        ('arch', arch.lower()),
        ('repo', repo.lower()),
        ('q',    name),
    ]
    # only include non-blank values in the query we generate
    pkg_data = [(x, y.encode('utf-8')) for x, y in pkg_data if y]
    return redirect("/packages/?%s" % urlencode(pkg_data))


def details(request, name='', repo='', arch=''):
    if all([name, repo, arch]):
        arch_obj = get_object_or_404(Arch, name=arch)
        repo_obj = get_object_or_404(Repo, name__iexact=repo)
        try:
            pkg = Package.objects.select_related(
                    'arch', 'repo', 'packager').get(pkgname=name,
                    repo=repo_obj, arch=arch_obj)
            if request.method == 'HEAD':
                return empty_response()
            return render(request, 'packages/details.html', {'pkg': pkg})
        except Package.DoesNotExist:
            # attempt a variety of fallback options before 404ing
            options = (redirect_agnostic, split_package_details,
                    recently_removed_package, replaced_package)
            for method in options:
                ret = method(request, name, repo_obj, arch_obj)
                if ret:
                    return ret
            # we've tried everything at this point, nothing to see
            raise Http404
    else:
        return redirect_to_search(request, name, repo, arch)


def groups(request, arch=None):
    arches = []
    if arch:
        get_object_or_404(Arch, name=arch, agnostic=False)
        arches.append(arch)
    grps = get_group_info(arches)
    context = {
        'groups': grps,
        'arch': arch,
    }
    return render(request, 'packages/groups.html', context)


def group_details(request, arch, name):
    arch = get_object_or_404(Arch, name=arch)
    arches = arch_plus_agnostic(arch)
    pkgs = Package.objects.normal().filter(
            groups__name=name, arch__in=arches).order_by('pkgname')
    if len(pkgs) == 0:
        raise Http404
    context = {
        'list_title': 'Group Details',
        'name': name,
        'arch': arch,
        'packages': pkgs,
    }
    return render(request, 'packages/packages_list.html', context)


def files(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    # files are inserted in sorted order, so preserve that
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('id')
    dir_count = sum(1 for f in fileslist if f.is_directory)
    files_count = len(fileslist) - dir_count
    context = {
        'pkg': pkg,
        'files': fileslist,
        'files_count': files_count,
        'dir_count': dir_count,
    }
    template = 'packages/files.html'
    return render(request, template, context)


def details_json(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    to_json = json.dumps(pkg, ensure_ascii=False, cls=PackageJSONEncoder)
    return HttpResponse(to_json, content_type='application/json')


def files_json(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    # files are inserted in sorted order, so preserve that
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('id')
    dir_count = sum(1 for f in fileslist if f.is_directory)
    files_count = len(fileslist) - dir_count
    data = {
        'pkgname': pkg.pkgname,
        'repo': pkg.repo.name.lower(),
        'arch': pkg.arch.name.lower(),
        'pkg_last_update': pkg.last_update,
        'files_last_update': pkg.files_last_update,
        'files_count': files_count,
        'dir_count': dir_count,
        'files': fileslist,
    }
    to_json = json.dumps(data, ensure_ascii=False, cls=PackageJSONEncoder)
    return HttpResponse(to_json, content_type='application/json')


def download(request, name, repo, arch):
    pkg = get_object_or_404(Package.objects.normal(),
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    url = get_mirror_url_for_download()
    if not url:
        raise Http404
    arch = pkg.arch.name
    if pkg.arch.agnostic:
        # grab the first non-any arch to fake the download path
        arch = Arch.objects.exclude(agnostic=True)[0].name
    url = '{host}{repo}/os/{arch}/{filename}'.format(host=url.url,
            repo=pkg.repo.name.lower(), arch=arch, filename=pkg.filename)
    return redirect(url)

# vim: set ts=4 sw=4 et:

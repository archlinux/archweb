import json
from collections import defaultdict

from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from api.schemas.packages import (
    PackageFilesSchema,
    PackageSchema,
    PackageSearchSchema,
)
from main.models import Package, PackageFile, Soname
from packages.models import PackageRelation
from packages.utils import DEPENDENCY_TYPES, PackageJSONEncoder, attach_maintainers
from packages.views.search import PackageSearchForm, parse_form

router = Router(tags=["packages"])


def _pkg_to_schema(pkg: Package) -> PackageSchema:
    all_deps = list(pkg.depends.all())
    deps_by_type = {
        name: [str(d) for d in all_deps if d.deptype == deptype]
        for deptype, name in DEPENDENCY_TYPES
    }
    return PackageSchema(
        pkgname=pkg.pkgname,
        pkgbase=pkg.pkgbase,
        repo=pkg.repo.name.lower(),
        arch=pkg.arch.name.lower(),
        pkgver=pkg.pkgver,
        pkgrel=pkg.pkgrel,
        epoch=pkg.epoch,
        pkgdesc=pkg.pkgdesc or None,
        url=pkg.url or None,
        filename=pkg.filename,
        compressed_size=pkg.compressed_size,
        installed_size=pkg.installed_size,
        build_date=pkg.build_date,
        last_update=pkg.last_update,
        flag_date=pkg.flag_date,
        maintainers=[u.username for u in pkg.maintainers],
        packager=pkg.packager.username if pkg.packager else None,
        groups=[g.name for g in pkg.groups.all()],
        licenses=[lic.name for lic in pkg.licenses.all()],
        conflicts=[str(c) for c in pkg.conflicts.all()],
        provides=[str(p) for p in pkg.provides.all()],
        replaces=[str(r) for r in pkg.replaces.all()],
        depends=deps_by_type['depends'],
        optdepends=deps_by_type['optdepends'],
        makedepends=deps_by_type['makedepends'],
        checkdepends=deps_by_type['checkdepends'],
    )


def _get_package(name: str, repo: str, arch: str) -> Package:
    return get_object_or_404(
        Package.objects.normal(),
        pkgname=name, repo__name__iexact=repo, arch__name=arch,
    )


@router.get("/search/", response=PackageSearchSchema, url_name="package-search")
def search(request):
    limit = 250
    container = {
        'version': 2,
        'limit': limit,
        'valid': False,
        'results': [],
    }

    if request.GET:
        form = PackageSearchForm(data=request.GET,
                                 show_staging=request.user.is_authenticated)
        if form.is_valid():
            form_limit = form.cleaned_data.get('limit', limit)
            limit = min(limit, form_limit) if form_limit else limit
            container['limit'] = limit

            packages = Package.objects.select_related('arch', 'repo', 'packager')
            if not request.user.is_authenticated:
                packages = packages.filter(repo__staging=False)
            packages = parse_form(form, packages)

            paginator = Paginator(packages, limit)
            container['num_pages'] = paginator.num_pages
            container['count'] = paginator.count

            page = form.cleaned_data.get('page')
            try:
                page = int(page) if page else 1
            except ValueError:
                return HttpResponseBadRequest('page parameter is not a number')
            container['page'] = page
            try:
                packages = paginator.page(page)
            except PageNotAnInteger:
                packages = paginator.page(1)
            except EmptyPage:
                packages = paginator.page(paginator.num_pages)

            attach_maintainers(packages)
            container['results'] = packages
            container['valid'] = True

    to_json = json.dumps(container, ensure_ascii=False, cls=PackageJSONEncoder)
    return HttpResponse(to_json, content_type='application/json')


@router.get("/{repo}/{arch}/{name}/", response=PackageSchema, url_name="package-details")
def details(request, repo: str, arch: str, name: str):
    return _pkg_to_schema(_get_package(name, repo, arch))


@router.get("/{repo}/{arch}/{name}/files/", response=PackageFilesSchema, url_name="package-files")
def files(request, repo: str, arch: str, name: str):
    pkg = _get_package(name, repo, arch)
    # files are inserted in sorted order, so preserve that
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('id')
    dir_count = sum(1 for f in fileslist if f.is_directory)
    files_count = len(fileslist) - dir_count
    return PackageFilesSchema(
        pkgname=pkg.pkgname,
        repo=pkg.repo.name.lower(),
        arch=pkg.arch.name.lower(),
        pkg_last_update=pkg.last_update,
        files_last_update=pkg.files_last_update,
        files_count=files_count,
        dir_count=dir_count,
        files=[f.directory + (f.filename or '') for f in fileslist],
    )


@router.get("/{repo}/{arch}/{name}/sonames/", response=list[str], url_name="package-sonames")
def sonames(request, repo: str, arch: str, name: str):
    pkg = _get_package(name, repo, arch)
    return list(Soname.objects.filter(pkg=pkg).values_list('name', flat=True))


@router.get("/pkgbase-maintainer", response=dict[str, list[str]], url_name="pkgbase-maintainer")
def pkgbase_maintainer(request):
    pkgbases = Package.objects.all().values('pkgbase')
    rels = PackageRelation.objects.filter(
        type=PackageRelation.MAINTAINER, pkgbase__in=pkgbases
    ).values_list('pkgbase', 'user_id').order_by().distinct()

    user_ids = {rel[1] for rel in rels}
    users = User.objects.in_bulk(user_ids)

    maintainers = defaultdict(list)
    for pkgbase_name, user_id in rels:
        maintainers[pkgbase_name].append(users[user_id].username)

    mapping = {}
    for row in pkgbases:
        pkgbase_name = row['pkgbase']
        if pkgbase_name not in mapping:
            mapping[pkgbase_name] = maintainers[pkgbase_name]
    return mapping

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers
from django.views.generic.simple import direct_to_template

from string import Template
from urllib import urlencode

from main.models import Package, PackageFile, Arch, Repo
from mirrors.models import MirrorUrl
from ..models import PackageRelation, PackageGroup
from ..utils import (get_group_info, get_differences_info,
        multilib_differences, get_wrong_permissions)

# make other views available from this same package
from .flag import flaghelp, flag, flag_confirmed, unflag, unflag_all
from .search import search
from .signoff import signoffs, signoff_package, signoff_options, signoffs_json


class PackageJSONEncoder(DjangoJSONEncoder):
    pkg_attributes = [ 'pkgname', 'pkgbase', 'repo', 'arch', 'pkgver',
            'pkgrel', 'epoch', 'pkgdesc', 'url', 'filename', 'compressed_size',
            'installed_size', 'build_date', 'last_update', 'flag_date' ]

    def default(self, obj):
        if hasattr(obj, '__iter__'):
            # mainly for queryset serialization
            return list(obj)
        if isinstance(obj, Package):
            data = dict((attr, getattr(obj, attr))
                    for attr in self.pkg_attributes)
            data['groups'] = obj.groups.all()
            return data
        if isinstance(obj, PackageFile):
            filename = obj.filename or ''
            return obj.directory + filename
        if isinstance(obj, (Repo, Arch, PackageGroup)):
            return obj.name.lower()
        return super(PackageJSONEncoder, self).default(obj)

def opensearch(request):
    if request.is_secure():
        domain = "https://%s" % request.META['HTTP_HOST']
    else:
        domain = "http://%s" % request.META['HTTP_HOST']

    return direct_to_template(request, 'packages/opensearch.xml',
            {'domain': domain},
            mimetype='application/opensearchdescription+xml')

@permission_required('main.change_package')
@require_POST
def update(request):
    ids = request.POST.getlist('pkgid')
    count = 0

    if request.POST.has_key('adopt'):
        repos = request.user.userprofile.allowed_repos.all()
        pkgs = Package.objects.filter(id__in=ids, repo__in=repos)
        disallowed_pkgs = Package.objects.filter(id__in=ids).exclude(
                repo__in=repos)

        if disallowed_pkgs:
            messages.warning(request,
                    "You do not have permission to adopt: %s." % (
                        ' '.join([p.pkgname for p in disallowed_pkgs])
                        ))

        for pkg in pkgs:
            if request.user not in pkg.maintainers:
                prel = PackageRelation(pkgbase=pkg.pkgbase,
                        user=request.user,
                        type=PackageRelation.MAINTAINER)
                count += 1
                prel.save()

        messages.info(request, "%d base packages adopted." % count)

    elif request.POST.has_key('disown'):
        # allow disowning regardless of allowed repos, helps things like
        # [community] -> [extra] moves
        for pkg in Package.objects.filter(id__in=ids):
            if request.user in pkg.maintainers:
                rels = PackageRelation.objects.filter(pkgbase=pkg.pkgbase,
                        user=request.user,
                        type=PackageRelation.MAINTAINER)
                count += rels.count()
                rels.delete()

        messages.info(request, "%d base packages disowned." % count)

    else:
        messages.error(request, "Are you trying to adopt or disown?")
    return redirect('/packages/')

def details(request, name='', repo='', arch=''):
    if all([name, repo, arch]):
        try:
            pkg = Package.objects.select_related(
                    'arch', 'repo', 'packager').get(pkgname=name,
                    repo__name__iexact=repo, arch__name=arch)
            return direct_to_template(request, 'packages/details.html',
                    {'pkg': pkg, })
        except Package.DoesNotExist:
            arch = get_object_or_404(Arch, name=arch)
            arches = [ arch ]
            arches.extend(Arch.objects.filter(agnostic=True))
            repo = get_object_or_404(Repo, name__iexact=repo)
            pkgs = Package.objects.normal().filter(pkgbase=name,
                    repo__testing=repo.testing, repo__staging=repo.staging,
                    arch__in=arches).order_by('pkgname')
            if len(pkgs) == 0:
                raise Http404
            context = {
                'list_title': 'Split Package Details',
                'name': name,
                'arch': arch,
                'packages': pkgs,
            }
            return direct_to_template(request, 'packages/packages_list.html',
                    context)
    else:
        pkg_data = [
            ('arch', arch.lower()),
            ('repo', repo.lower()),
            ('q',    name),
        ]
        # only include non-blank values in the query we generate
        pkg_data = [(x, y) for x, y in pkg_data if y]
        return redirect("/packages/?%s" % urlencode(pkg_data))

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
    return direct_to_template(request, 'packages/groups.html', context)

def group_details(request, arch, name):
    arch = get_object_or_404(Arch, name=arch)
    arches = [ arch ]
    arches.extend(Arch.objects.filter(agnostic=True))
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
    return direct_to_template(request, 'packages/packages_list.html', context)

@vary_on_headers('X-Requested-With')
def files(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('directory', 'filename')
    dir_count = sum(1 for f in fileslist if f.is_directory)
    files_count = len(fileslist) - dir_count
    context = {
        'pkg': pkg,
        'files': fileslist,
        'files_count': files_count,
        'dir_count': dir_count,
    }
    template = 'packages/files.html'
    if request.is_ajax():
        template = 'packages/files_list.html'
    return direct_to_template(request, template, context)

def details_json(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    to_json = simplejson.dumps(pkg, ensure_ascii=False,
            cls=PackageJSONEncoder)
    return HttpResponse(to_json, mimetype='application/json')

def files_json(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('directory', 'filename')
    data = {
        'pkgname': pkg.pkgname,
        'repo': pkg.repo.name.lower(),
        'arch': pkg.arch.name.lower(),
        'files': fileslist,
    }
    to_json = simplejson.dumps(data, ensure_ascii=False,
            cls=PackageJSONEncoder)
    return HttpResponse(to_json, mimetype='application/json')

def download(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    mirror_urls = MirrorUrl.objects.filter(
            mirror__public=True, mirror__active=True,
            protocol__protocol__iexact='HTTP')
    # look first for an 'Any' URL, then fall back to any HTTP URL
    filtered_urls = mirror_urls.filter(mirror__country='Any')[:1]
    if not filtered_urls:
        filtered_urls = mirror_urls[:1]
    if not filtered_urls:
        raise Http404
    arch = pkg.arch.name
    if pkg.arch.agnostic:
        # grab the first non-any arch to fake the download path
        arch = Arch.objects.exclude(agnostic=True)[0].name
    values = {
        'host': filtered_urls[0].url,
        'arch': arch,
        'repo': pkg.repo.name.lower(),
        'file': pkg.filename,
    }
    url = Template('${host}${repo}/os/${arch}/${file}').substitute(values)
    return redirect(url)

def arch_differences(request):
    # TODO: we have some hardcoded magic here with respect to the arches.
    arch_a = Arch.objects.get(name='i686')
    arch_b = Arch.objects.get(name='x86_64')
    differences = get_differences_info(arch_a, arch_b)
    multilib_diffs = multilib_differences()
    context = {
            'arch_a': arch_a,
            'arch_b': arch_b,
            'differences': differences,
            'multilib_differences': multilib_diffs
    }
    return direct_to_template(request, 'packages/differences.html', context)

@permission_required('main.change_package')
@never_cache
def stale_relations(request):
    relations = PackageRelation.objects.select_related('user')
    pkgbases = Package.objects.all().values('pkgbase')

    inactive_user = relations.filter(user__is_active=False)
    missing_pkgbase = relations.exclude(
            pkgbase__in=pkgbases).order_by('pkgbase')
    wrong_permissions = get_wrong_permissions()

    context = {
            'inactive_user': inactive_user,
            'missing_pkgbase': missing_pkgbase,
            'wrong_permissions': wrong_permissions,
    }
    return direct_to_template(request, 'packages/stale_relations.html', context)

@permission_required('packages.delete_packagerelation')
@require_POST
def stale_relations_update(request):
    ids = set(request.POST.getlist('relation_id'))

    if ids:
        PackageRelation.objects.filter(id__in=ids).delete()

    messages.info(request, "%d package relations deleted." % len(ids))
    return redirect('/packages/stale_relations/')

# vim: set ts=4 sw=4 et:

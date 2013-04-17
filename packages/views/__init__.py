import hashlib
import json

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe, require_POST

from main.models import Package, Arch
from ..models import PackageRelation
from ..utils import (get_differences_info,
        multilib_differences, get_wrong_permissions)

# make other views available from this same package
from .display import (details, groups, group_details, files, details_json,
        files_json, download)
from .flag import flaghelp, flag, flag_confirmed, unflag, unflag_all
from .search import search_json
from .signoff import signoffs, signoff_package, signoff_options, signoffs_json


@require_safe
@cache_control(public=True, max_age=86400)
def opensearch(request):
    if request.is_secure():
        domain = "https://%s" % request.META['HTTP_HOST']
    else:
        domain = "http://%s" % request.META['HTTP_HOST']

    return render(request, 'packages/opensearch.xml',
            {'domain': domain},
            content_type='application/opensearchdescription+xml')


@require_safe
@cache_control(public=True, max_age=300)
def opensearch_suggest(request):
    search_term = request.GET.get('q', '')
    if search_term == '':
        return HttpResponse('', content_type='application/x-suggestions+json')

    cache_key = 'opensearch:packages:' + \
            hashlib.md5(search_term.encode('utf-8')).hexdigest()
    to_json = cache.get(cache_key, None)
    if to_json is None:
        q = Q(pkgname__startswith=search_term)
        lookup = search_term.lower()
        if search_term != lookup:
            # package names are lowercase by convention, so include that in
            # search if original wasn't lowercase already
            q |= Q(pkgname__startswith=lookup)
        names = Package.objects.filter(q).values_list(
                'pkgname', flat=True).order_by('pkgname').distinct()[:10]
        results = [search_term, list(names)]
        to_json = json.dumps(results, ensure_ascii=False)
        cache.set(cache_key, to_json, 300)
    return HttpResponse(to_json, content_type='application/x-suggestions+json')


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
    return render(request, 'packages/differences.html', context)

@permission_required('main.change_package')
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
    return render(request, 'packages/stale_relations.html', context)

@permission_required('packages.delete_packagerelation')
@require_POST
def stale_relations_update(request):
    ids = set(request.POST.getlist('relation_id'))

    if ids:
        PackageRelation.objects.filter(id__in=ids).delete()

    messages.info(request, "%d package relations deleted." % len(ids))
    return redirect('/packages/stale_relations/')

# vim: set ts=4 sw=4 et:

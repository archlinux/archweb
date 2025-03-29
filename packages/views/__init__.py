import hashlib
import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST, require_safe

from main.models import Package, Soname
from packages.models import PackageRelation

from ..utils import get_wrong_permissions, multilib_differences


@require_safe
@cache_control(public=True, max_age=86400)
def opensearch(request):
    current_site = Site.objects.get_current()

    return render(request, 'packages/opensearch.xml',
                  {'domain': f'{request.scheme}://{current_site.domain}'},
                  content_type='application/opensearchdescription+xml')


@require_safe
@cache_control(public=True, max_age=613)
def opensearch_suggest(request):
    search_term = request.GET.get('q', '')
    if search_term == '':
        return HttpResponse('', content_type='application/x-suggestions+json')

    cache_key = 'opensearch:packages:' + hashlib.md5(search_term.encode('utf-8')).hexdigest()
    to_json = cache.get(cache_key, None)
    if to_json is None:
        # Package names are lowercase by convention
        q = Q(pkgname__istartswith=search_term)

        names = Package.objects.filter(q).values_list(
            'pkgname', flat=True).order_by('pkgname').distinct()[:10]
        results = (search_term, tuple(names))
        to_json = json.dumps(results, ensure_ascii=False)
        cache.set(cache_key, to_json, 613)
    return HttpResponse(to_json, content_type='application/x-suggestions+json')


@permission_required('main.change_package')
@require_POST
def update(request):
    ids = request.POST.getlist('pkgid')
    count = 0

    if 'adopt' in request.POST:
        repos = request.user.userprofile.allowed_repos.all()
        pkgs = Package.objects.filter(id__in=ids, repo__in=repos)
        disallowed_pkgs = Package.objects.filter(id__in=ids).exclude(
            repo__in=repos)

        if disallowed_pkgs:
            messages.warning(request,
                             "You do not have permission to adopt: %s." %
                             (' '.join([p.pkgname for p in disallowed_pkgs])))

        for pkg in pkgs:
            if request.user in pkg.maintainers:
                continue

            PackageRelation(pkgbase=pkg.pkgbase,
                            user=request.user,
                            type=PackageRelation.MAINTAINER).save()
            count += 1

        messages.info(request, "%d base packages adopted." % count)

    elif 'disown' in request.POST:
        # allow disowning regardless of allowed repos, helps things like
        # [community] -> [extra] moves
        for pkg in Package.objects.filter(id__in=ids):
            if request.user in pkg.maintainers:
                rels = PackageRelation.objects.filter(
                    pkgbase=pkg.pkgbase,
                    user=request.user,
                    type=PackageRelation.MAINTAINER
                )
                count += rels.count()
                rels.delete()

        messages.info(request, "%d base packages disowned." % count)

    else:
        messages.error(request, "Are you trying to adopt or disown?")
    return redirect('/packages/')


def arch_differences(request):
    context = {
        'multilib_differences': multilib_differences()
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


def sonames(request):
    if request.method == 'GET':
        packages = []
        name = request.GET.get('name')

        if name:
            sonames = Soname.objects.filter(name__startswith=name).values('pkg__pkgname',
                                                                          'pkg__pkgver',
                                                                          'pkg__pkgrel',
                                                                          'pkg__epoch',
                                                                          'pkg__repo__name')
            packages = [{'pkgname': soname['pkg__pkgname'], 'pkgrel': soname['pkg__pkgrel'],
                         'pkgver': soname['pkg__pkgver'], 'epoch': soname['pkg__epoch'],
                         'repo': soname['pkg__repo__name'].lower()} for soname in sonames]
        else:
            return HttpResponseBadRequest('name parameter is required')

        to_json = json.dumps(packages, ensure_ascii=False)
        return HttpResponse(to_json, content_type='application/json')

    else:
        return HttpResponseBadRequest('only GET is allowed')


@cache_control(public=True, max_age=300)
def pkgbase_mapping(request):
    if request.method == 'GET':
        pkgbases = Package.objects.all().values('pkgbase')
        rels = PackageRelation.objects.filter(type=PackageRelation.MAINTAINER,
                                              pkgbase__in=pkgbases).values_list(
                                                  'pkgbase', 'user_id').order_by().distinct()

        # get all the user objects we will need
        user_ids = {rel[1] for rel in rels}
        users = User.objects.in_bulk(user_ids)

        # now build a pkgbase -> [maintainers...] map
        maintainers = defaultdict(list)
        for rel in rels:
            user = users[rel[1]]
            maintainers[rel[0]].append(user.username)

        pkgbase_maintainer_mapping = {}
        for pkgbase in pkgbases:
            pkgbase = pkgbase['pkgbase']
            if pkgbase in pkgbase_maintainer_mapping:
                continue
            pkgbase_maintainer_mapping[pkgbase] = maintainers[pkgbase]

        to_json = json.dumps(pkgbase_maintainer_mapping, ensure_ascii=False)
        return HttpResponse(to_json, content_type='application/json')
    else:
        return HttpResponseBadRequest('only GET is allowed')

# vim: set ts=4 sw=4 et:

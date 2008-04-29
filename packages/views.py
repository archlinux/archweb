from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.template import Context, loader
from django.core import validators
from django.contrib.auth.models import User
from datetime import datetime
from archweb_dev.main.utils import validate, render_response
from archweb_dev.main.models import Package, PackageFile, PackageDepend
from archweb_dev.main.models import Arch, Repo
from django.core.exceptions import ObjectDoesNotExist


def update(request):
    if request.POST.has_key('adopt'):
        mode = 'adopt'
        message = 'Adoption was successful'
    if request.POST.has_key('disown'):
        mode = 'disown'
        message = 'Disown was successful'
    try:
        maint = User.objects.get(username=request.user.username)
    except User.DoesNotExist:
        return render_response(request, 'error_page.html', {'errmsg':'No maintainer record found!  Are you a maintainer?'})
    ids = request.POST.getlist('pkgid')
    for id in ids:
        pkg = Package.objects.get(id=id)
        if mode == 'adopt' and pkg.maintainer_id == 0:
            pkg.maintainer = maint
        elif mode == 'disown' and pkg.maintainer == maint:
            pkg.maintainer_id = 0
        else:
            message = "You are not the current maintainer"
        pkg.save()
    return render_response(request, 'status_page.html', {'message':message})

def details(request, pkgid=0, name='', repo=''):
    if pkgid == 0:
        p = Package.objects.filter(pkgname=name)
        if repo: p = p.filter(repo__name__iexact=repo)
        # if more then one result, send to the search view
        if len(p) > 1: return search(request, name)
        if len(p) < 1: return render_response(request, 'error_page.html',
            {'errmsg': 'No matching packages.'})
        pkgid = p[0].id

    pkg = get_object_or_404(Package, id=pkgid)
    return render_response(request, 'packages/details.html', {'pkg': pkg})

def search(request, query=''):
    if request.GET.has_key('q'):
        # take the q GET var over the one passed on the URL
        query = request.GET['q'].strip()

    # fetch the form vars
    repo       = request.GET.get('repo', 'all')
    arch       = request.GET.get('arch', 'all')
    lastupdate = request.GET.get('lastupdate', '')
    limit      = int(request.GET.get('limit', '50'))
    skip       = int(request.GET.get('skip', '0'))
    sort       = request.GET.get('sort', '')
    maint      = request.GET.get('maint', 'all')
    flagged_only = request.GET.get('flagged_only', 'n')

    # build the form lists
    repos = Repo.objects.all()
    arches  = Arch.objects.all()
    # copy GET data over and add the lists
    c = request.GET.copy()
    c['repos'], c['arches']  = repos, arches
    c['limit'], c['skip'] = limit, skip
    c['lastupdate'] = lastupdate
    c['sort'] = sort
    # 'q' gets renamed to 'query', so it's not in GET
    c['query'] = query

    # validate
    errors = {}
    validate(errors, 'Last Update', lastupdate, validators.isValidANSIDate, True, request)
    validate(errors, 'Page Limit', str(limit), validators.isOnlyDigits, True, request)
    validate(errors, 'Page Skip', str(skip), validators.isOnlyDigits, True, request)
    if errors:
        c['errors'] = errors
        return render_response(request, 'packages/search.html', c)

    if query:
        res1 = Package.objects.filter(pkgname__icontains=query)
        res2 = Package.objects.filter(pkgdesc__icontains=query)
        results = res1 | res2
    else:
        results = Package.objects.all()
    if repo != 'all' and repo in [x.name for x in repos]:
        results = results.filter(repo__name__iexact=repo)
    if arch != 'all' and arch in [x.name for x in arches]:
        results = results.filter(arch__name__iexact=arch)
    if maint != 'all':
        results = results.filter(maintainer=maint)
    if flagged_only != 'n':
        results = results.filter(needupdate=1)
    if lastupdate:
        results = results.filter(
            last_update__gte=datetime(
                int(lastupdate[0:4]),
                int(lastupdate[5:7]),
                int(lastupdate[8:10])))

    # sort results
    if sort == '':
        results = results.order_by('repo', 'arch', 'pkgname')
    else:
        # duplicate sort fields shouldn't hurt anything
        results = results.order_by(sort, 'repo', 'arch', 'pkgname')

    qs = request.GET.copy()
    # build pagination urls
    if results.count() > (skip + limit) and limit > 0:
        qs['skip'] = skip + limit
        c['nextpage'] = '?' + qs.urlencode()
    if skip > 0:
        qs['skip'] = max(0, skip - limit)
        c['prevpage'] = '?' + qs.urlencode()
    # pass the querystring to the template so we can build sort queries
    c['querystring'] = request.GET

    # if only there's only one result, pass right to the package details view
    if results.count() == 1: return details(request, results[0].id)
    # limit result set
    if limit > 0: results = results[skip:(skip+limit)]

    c['results'] = results
    return render_response(request, 'packages/search.html', c)

def files(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    files = PackageFile.objects.filter(pkg=pkgid)
    return render_response(request, 'packages/files.html', {'pkg':pkg,'files':files})

def unflag(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    pkg.needupdate = 0
    pkg.save()
    return HttpResponseRedirect('/packages/%d/' % (pkg.id))

# vim: set ts=4 sw=4 et:


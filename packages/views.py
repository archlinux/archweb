from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.template import Context, loader
from django.core import validators
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime
from archweb_dev.main.utils import validate, render_response
from archweb_dev.main.models import Package, PackageFile, Repo, Category
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
        if repo: p = p.filter(repo__name__exact=repo)
        # if more then one result, send to the search view
        if len(p) > 1: return search(request, name)
        if len(p) < 1: return render_response(request, 'error_page.html',
            {'errmsg': 'No matching packages.'})
        pkgid = p[0].id

    pkg = get_object_or_404(Package, id=pkgid)
    origin_repo = None
    if pkg.repo.name == 'Testing':
        try:
            origin_repo = Package.objects.filter(
                pkgname__exact = pkg.pkgname).exclude(
                    repo__name__exact = pkg.repo.name).get().repo.name
        except ObjectDoesNotExist:
            origin_repo = None
    return render_response(
        request, 
        'packages/details.html', 
        {'pkg': pkg, 'origin_repo': origin_repo})

def search(request, query=''):
    if request.GET.has_key('q'):
        # take the q GET var over the one passed on the URL
        query = request.GET['q'].strip()

    # fetch the form vars
    repo       = request.GET.get('repo', 'all')
    category   = request.GET.get('category', 'all')
    lastupdate = request.GET.get('lastupdate', '')
    limit      = int(request.GET.get('limit', '50'))
    skip       = int(request.GET.get('skip', '0'))
    sort       = request.GET.get('sort', '')
    maint      = request.GET.get('maint', 'all')

    # build the form lists
    repos = Repo.objects.order_by('name')
    cats  = Category.objects.order_by('category')
    # copy GET data over and add the lists
    c = request.GET.copy()
    c['repos'], c['categories']  = repos, cats
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
    if repo != 'all':     results = results.filter(repo__name__exact=repo)
    if category != 'all': results = results.filter(category__category__exact=category)
    if maint != 'all':    results = results.filter(maintainer=maint)
    if lastupdate:        results = results.filter(last_update__gte=datetime(int(lastupdate[0:4]),int(lastupdate[5:7]),int(lastupdate[8:10])))
    # select_related() shouldn't be needed -- we're working around a Django bug
    #results = results.select_related().order_by('repos.name', 'category', 'pkgname')

    # sort results
    if sort == '':
        results = results.order_by('repo', 'category', 'pkgname')
    else:
        # duplicate sort fields shouldn't hurt anything
        results = results.order_by(sort, 'repo', 'category', 'pkgname')

    qs = request.GET.copy()
    # build pagination urls
    if results.count() > (skip + limit):
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

def flaghelp(request):
    return render_response(request, 'packages/flaghelp.html')

def flag(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    context = {'pkg': pkg}
    if request.POST.has_key('confirmemail'):
        email = request.POST['confirmemail']
        if request.POST.has_key('usermessage'):
            message = request.POST['usermessage']
        else:
            message = None
        # validate
        errors = {}
        validate(errors, 'Email Address', email, validators.isValidEmail, False, request)
        if errors:
            context['errors'] = errors
            return render_response(request, 'packages/flag.html', context)

        context['confirmemail'] = email
        pkg.needupdate = 1
        pkg.save()
        if pkg.maintainer_id > 0:
            # send notification email to the maintainer
            t = loader.get_template('packages/outofdate.txt')
            c = Context({
                'email':   request.POST['confirmemail'],
                'message': message,
                'pkgname': pkg.pkgname,
                'weburl':  'http://www.archlinux.org/packages/' + str(pkg.id) + '/'
            })
            send_mail('arch: Package [%s] marked out-of-date' % pkg.pkgname, 
                    t.render(c), 
                    'Arch Website Notification <nobody@archlinux.org>',
                    [pkg.maintainer.email],
                    fail_silently=True)
    return render_response(request, 'packages/flag.html', context)

@login_required
def unflag(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    if pkg.maintainer_id == 0 or \
        pkg.maintainer.username != request.user.username:
        return render_response(request, 'error_page.html', {'errmsg': 'You do not own this package.'})
    pkg.needupdate = 0
    pkg.save()
    return HttpResponseRedirect('/packages/%d/' % (pkg.id))

# vim: set ts=4 sw=4 et:


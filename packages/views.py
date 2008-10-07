import urllib
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.admin.widgets import AdminDateWidget
from django.views.generic import list_detail
from django.db.models import Q
import datetime
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import Package, PackageFile
from archweb_dev.main.models import Arch, Repo, Signoff
from archweb_dev.main.utils import make_choice

def update(request):
    if request.POST.has_key('adopt'):
        mode = 'adopt'
        message = 'Adoption was successful'
    if request.POST.has_key('disown'):
        mode = 'disown'
        message = 'Disown was successful'

    ids = request.POST.getlist('pkgid')
    for id in ids:
        pkg = Package.objects.get(id=id)
        if mode == 'adopt':
            pkg.maintainer = request.user
        elif mode == 'disown':
            pkg.maintainer_id = 0
        pkg.save()
    return render_response(request, 'status_page.html', {'message':message})

def details(request, pkgid=0, name='', repo='', arch=''):
    if pkgid != 0:
        pkg = get_object_or_404(Package, id=pkgid)
    elif all([name, repo, arch]):
        pkg= get_object_or_404(Package,
                pkgname=name, repo__name__iexact=repo, arch__name=arch)
    else:
        p = Package.objects.filter(pkgname=name)
        if repo: p = p.filter(repo__name__iexact=repo)
        lenp = p.count()
        # if more then one result, send to the search view
        if lenp > 1: return search(request, name)
        if lenp < 1: return render_response(request, 'error_page.html',
            {'errmsg': 'No matching packages.'})
        pkg = p[0]

    return render_response(request, 'packages/details.html', {'pkg': pkg})


class PackageSearchForm(forms.Form):
    repo = forms.ChoiceField(required=False)
    arch = forms.ChoiceField(required=False)
    q = forms.CharField(required=False)
    maintainer = forms.ChoiceField(required=False)
    last_update = forms.DateField(required=False, widget=AdminDateWidget())
    flagged = forms.ChoiceField(
            choices=[('', 'All')] + make_choice(['Flagged', 'Not Flagged']),
            required=False)
    limit = forms.ChoiceField(
            choices=make_choice([50, 100, 250]) + [('all', 'All')],
            required=False,
            initial=50)

    def clean_limit(self):
        limit = self.cleaned_data['limit']
        if limit == 'all':
            limit = None
        elif limit:
            try:
                limit = int(limit)
            except:
                raise forms.ValidationError("Should be an integer")
        else:
            limit = 50
        return limit


    def __init__(self, *args, **kwargs):
        super(PackageSearchForm, self).__init__(*args, **kwargs)
        self.fields['repo'].choices = self.fields[
                'repo'].widget.choices = [('', 'All')] + make_choice(
                        [repo.name for repo in Repo.objects.all()])
        self.fields['arch'].choices = self.fields[
                'arch'].widget.choices = [('', 'All')] + make_choice(
                        [arch.name for arch in Arch.objects.all()])
        self.fields['maintainer'].choices = self.fields[
                'maintainer'].widget.choices = [
                        ('', 'All'), ('orphan', 'Orphan')] + make_choice(
                        [m.username for m in User.objects.all()])

def search(request, page=None):
    current_query = '?'
    limit=50
    packages = Package.objects.all()

    if request.GET:
        current_query += urllib.urlencode(request.GET)
        form = PackageSearchForm(data=request.GET)
        if form.is_valid():
            if form.cleaned_data['repo']:
                packages = packages.filter(
                        repo__name=form.cleaned_data['repo'])
            if form.cleaned_data['arch']:
                packages = packages.filter(
                        arch__name=form.cleaned_data['arch'])
            if form.cleaned_data['maintainer'] == 'orphan':
                packages=packages.filter(maintainer__id = 0)
            if form.cleaned_data['flagged'] == 'Flagged':
                packages=packages.filter(needupdate=True)
            elif form.cleaned_data['flagged'] == 'Not Flagged':
                packages = packages.filter(needupdate=False)
            elif form.cleaned_data['maintainer']:
                packages = packages.filter(
                    maintainer__username=form.cleaned_data['maintainer'])
            limit = form.cleaned_data['limit']
            if form.cleaned_data['q']:
                query = form.cleaned_data['q']
                q = Q(pkgname__icontains=query) | Q(pkgdesc__icontains=query)
                packages = packages.filter(q)
            if form.cleaned_data['last_update']:
                lu = form.cleaned_data['last_update']
                packages = packages.filter(last_update__gte=
                        datetime.datetime(lu.year, lu.month, lu.day, 0, 0))
    else:
        form = PackageSearchForm()

    page_dict = {'search_form': form,
            'current_query': current_query
            }
    if len(packages) == 1:
        return HttpResponseRedirect(packages[0].get_absolute_url())

    sort = request.GET.get('sort', '')
    if sort in request.GET:
        packages = packages.order_by(sort, 'repo', 'arch', 'pkgname')
    else:
        packages = packages.order_by('repo', 'arch', '-last_update', 'pkgname')

    return list_detail.object_list(request, packages,
            template_name="packages/search.html",
            page=page,
            paginate_by=limit,
            template_object_name="package",
            extra_context=page_dict)
    
    # OLD IMPLEMENTATION BELOW HERE
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
    users = User.objects.all()
    # copy GET data over and add the lists
    c = request.GET.copy()
    c['repos'], c['arches']  = repos, arches
    c['users'] = users
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
            last_update__gte=datetime.datetime(
                int(lastupdate[0:4]),
                int(lastupdate[5:7]),
                int(lastupdate[8:10])))

    # sort results
    if sort == '':
        results = results.order_by('repo', 'arch', '-last_update', 'pkgname')
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

def signoffs(request, message=None):
    packages = Package.objects.filter(repo__name="Testing").order_by("pkgname")
    return render_response(request, 'packages/signoffs.html',
            {'packages': packages, 'message': message})

def signoff_package(request, arch, pkgname):
    pkg = get_object_or_404(Package,
            arch__name=arch,
            pkgname=pkgname,
            repo__name="Testing")

    signoff, created = Signoff.objects.get_or_create(
            pkg=pkg,
            pkgver=pkg.pkgver,
            pkgrel=pkg.pkgrel,
            packager=request.user)

    if created:
        message = "You have successfully signed off for %s on %s" % (
                pkg.pkgname, pkg.arch)
    else:
        message = "You have already signed off for %s on %s" % (
                pkg.pkgname, pkg.arch)

    return signoffs(request, message)



# vim: set ts=4 sw=4 et:


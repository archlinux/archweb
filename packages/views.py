from django import forms
from itertools import chain
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.forms.util import flatatt
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.contrib.admin.widgets import AdminDateWidget
from datetime import datetime
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import Package, PackageFile
from archweb_dev.main.models import Arch, Repo, Signoff


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


class EmptySelectWidget(forms.widgets.Select):
    '''Like any select box but allows you to use a custom string for the
    'empty' field.'''
    def __init__(self, empty_string="All", attrs=None, choices=()):
        self.empty_string = empty_string
        super(EmptySelectWidget, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select%s>' % flatatt(final_attrs)]
        # Normalize to string.
        str_value = force_unicode(value)
        for option_value, option_label in chain(self.choices, choices):
            if option_value == '':
                option_label = self.empty_string
            option_value = force_unicode(option_value)
            selected_html = (
                option_value == str_value) and u' selected="selected"' or ''
            output.append(u'<option value="%s"%s>%s</option>' % (
                    escape(option_value), selected_html,
                    conditional_escape(force_unicode(option_label))))
        output.append(u'</select>')
        return mark_safe(u'\n'.join(output))

class PackageSearchForm(forms.Form):
    repo = forms.ModelChoiceField(Repo.objects.all(),
            widget=EmptySelectWidget, required=False)
    arch = forms.ModelChoiceField(Arch.objects.all(),
            widget=EmptySelectWidget, required=False)
    keywords = forms.CharField(required=False)
    maintainer = forms.ModelChoiceField(User.objects.all(),
            widget=EmptySelectWidget, required=False)
    last_update = forms.DateField(required=False, widget=AdminDateWidget())
    limit = forms.ChoiceField(choices=[
        ('50', '50'),
        ('100', '100'),
        ('250', '250'),
        ('All', 'All')], required=False)

def search(request):
    if request.GET:
        form = PackageSearchForm(data=request.GET)
        if form.is_valid():
            pass
    else:
        form = PackageSearchForm()

    page_dict = {'search_form': form}
    return render_to_response('packages/search.html',
            RequestContext(request, page_dict))
    


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
            last_update__gte=datetime(
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


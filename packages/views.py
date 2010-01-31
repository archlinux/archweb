import urllib
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.widgets import AdminDateWidget
from django.views.generic import list_detail
from django.db.models import Q
import datetime
from archweb.main.models import Package, PackageFile
from archweb.main.models import Arch, Repo, Signoff
from archweb.main.utils import make_choice


@permission_required('main.change_package')
def update(request):
    ids = request.POST.getlist('pkgid')
    mode = None
    if request.POST.has_key('adopt'):
        mode = 'adopt'
        maint = request.user
    if request.POST.has_key('disown'):
        mode = 'disown'
        maint = None

    if mode:
        pkgs = Package.objects.filter(
                id__in=ids,
                repo__in=request.user.userprofile_user.all(
                    )[0].allowed_repos.all())
        disallowed_pkgs = Package.objects.filter(id__in=ids).exclude(
                repo__in=request.user.userprofile_user.all(
                    )[0].allowed_repos.all())
        for pkg in pkgs:
            pkg.maintainer = maint
            pkg.save()

        request.user.message_set.create(message="%d packages %sed" % (
            len(pkgs), mode))
        if disallowed_pkgs:
            request.user.message_set.create(
                    message="You do not have permmission to adopt: %s" % (
                        ' '.join([p.pkgname for p in disallowed_pkgs])
                        ))
    else:
        request.user.message_set.create(message="update called without adopt/disown")
    return HttpResponseRedirect('/packages/')

def details(request, name='', repo='', arch=''):
    if all([name, repo, arch]):
        pkg= get_object_or_404(Package,
                pkgname=name, repo__name__iexact=repo, arch__name=arch)
        return render_to_response('packages/details.html', RequestContext(
            request, {'pkg': pkg, }))
    else:
        return HttpResponseRedirect("/packages/?arch=%s&repo=%s&q=%s" % (
            arch.lower(), repo.title(), name))

def getmaintainer(request, name, repo, arch):
    "Returns the maintainer as a plaintext."

    pkg= get_object_or_404(Package, 
        pkgname=name, repo__name__iexact=repo, arch__name=arch)

    return HttpResponse(str(pkg.maintainer))

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
        self.fields['q'].widget.attrs.update({"size": "30"})
        self.fields['maintainer'].choices = self.fields[
                'maintainer'].widget.choices = [
                        ('', 'All'), ('orphan', 'Orphan')] + make_choice(
                        [m.username for m in User.objects.order_by('username')])

def search(request, page=None):
    current_query = '?'
    limit=50
    packages = Package.objects.all()

    if request.GET:
        # urlencode can't handle unicode. One fix for this is to call:
        # urllib.urlencode(request.GET, doseq), which has a side effect of
        # converting unicode to ascii, and replacing unknown characters with ?.
        # Using UTF8 seems to work just as well without data loss.
        encoded = {}
        for key in request.GET:
            encoded[key] = request.GET[key].encode('UTF8')
        current_query += urllib.urlencode(encoded)
        form = PackageSearchForm(data=request.GET)
        if form.is_valid():
            if form.cleaned_data['repo']:
                packages = packages.filter(
                        repo__name=form.cleaned_data['repo'])
            if form.cleaned_data['arch']:
                packages = packages.filter(
                        arch__name=form.cleaned_data['arch'])
            if form.cleaned_data['maintainer'] == 'orphan':
                packages=packages.filter(maintainer=None)
            elif form.cleaned_data['maintainer']:
                packages = packages.filter(
                    maintainer__username=form.cleaned_data['maintainer'])
            if form.cleaned_data['flagged'] == 'Flagged':
                packages=packages.filter(needupdate=True)
            elif form.cleaned_data['flagged'] == 'Not Flagged':
                packages = packages.filter(needupdate=False)
            if form.cleaned_data['q']:
                query = form.cleaned_data['q']
                q = Q(pkgname__icontains=query) | Q(pkgdesc__icontains=query)
                packages = packages.filter(q)
            if form.cleaned_data['last_update']:
                lu = form.cleaned_data['last_update']
                packages = packages.filter(last_update__gte=
                        datetime.datetime(lu.year, lu.month, lu.day, 0, 0))
            limit = form.cleaned_data['limit']
    else:
        form = PackageSearchForm()

    page_dict = {'search_form': form,
            'current_query': current_query
            }
    if len(packages) == 1:
        return HttpResponseRedirect(packages[0].get_absolute_url())

    allowed_sort = ["arch", "repo", "pkgname", "maintainer", "last_update"]
    allowed_sort += ["-" + s for s in allowed_sort]
    sort = request.GET.get('sort', None)
    if sort in allowed_sort:
        packages = packages.order_by(
                request.GET['sort'], 'repo', 'arch', 'pkgname')
        page_dict['sort'] = sort
    else:
        packages = packages.order_by('repo', 'arch', '-last_update', 'pkgname')


    return list_detail.object_list(request, packages,
            template_name="packages/search.html",
            page=page,
            paginate_by=limit,
            template_object_name="package",
            extra_context=page_dict)

def files(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    files = PackageFile.objects.filter(pkg=pkgid)
    return render_to_response('packages/files.html', RequestContext(request, {'pkg':pkg,'files':files}))

@permission_required('main.change_package')
def unflag(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    pkg.needupdate = 0
    pkg.save()
    return HttpResponseRedirect(pkg.get_absolute_url())

@permission_required('main.change_package')
def signoffs(request):
    packages = Package.objects.filter(repo__name="Testing").order_by("pkgname")
    package_list = []
    other_packages = Package.objects.exclude(repo__name="Testing")
    for package in packages:
        other_package = other_packages.filter(pkgname=package.pkgname)
        if len(other_package):
            repo = other_package[0].repo.name
        else:
            repo = "Unknown"
        package_list.append((package, repo))
    return render_to_response('packages/signoffs.html',
            RequestContext(request, {'packages': package_list}))

@permission_required('main.change_package')
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

    message = "You have successfully" if created else "You have already"
    request.user.message_set.create(
            message="%s signed off for %s on %s" % (
            message, pkg.pkgname, pkg.arch))

    return signoffs(request)

def flaghelp(request):
    return render_to_response('packages/flaghelp.html')

class FlagForm(forms.Form):
    email = forms.EmailField(label='* E-mail Address')
    usermessage = forms.CharField(label='Message To Dev',
            widget=forms.Textarea, required=False)
    # The field below is used to filter out bots that blindly fill out all input elements
    website = forms.CharField(label='',
            widget=forms.TextInput(attrs={'style': 'display:none;'}),
            required=False)

def flag(request, pkgid):
    pkg = get_object_or_404(Package, id=pkgid)
    context = {'pkg': pkg}
    if pkg.needupdate == 1:
        # already flagged. do nothing.
        return render_to_response('packages/flagged.html', context)

    if request.POST:
        form = FlagForm(request.POST)
        if form.is_valid() and form.cleaned_data['website'] == '':
            # flag all architectures
            pkgs = Package.objects.filter(
                    pkgname=pkg.pkgname, repo=pkg.repo)
            for package in pkgs:
                package.needupdate = 1
                package.save()

            if not pkg.maintainer:
                toemail = 'arch-notifications@archlinux.org'
                subject = 'Orphan %s package [%s] marked out-of-date' % (pkg.repo.name, pkg.pkgname)
            else:
                toemail = pkg.maintainer.email
                subject = '%s package [%s] marked out-of-date' % (pkg.repo.name, pkg.pkgname)

            # send notification email to the maintainer
            t = loader.get_template('packages/outofdate.txt')
            c = Context({
                'email': form.cleaned_data['email'],
                'message': form.cleaned_data['usermessage'],
                'pkg': pkg,
                'weburl': 'http://www.archlinux.org'+ pkg.get_absolute_url()
            })
            send_mail(subject,
                    t.render(c), 
                    'Arch Website Notification <nobody@archlinux.org>',
                    [toemail],
                    fail_silently=True)
            context['confirmed'] = True
    else:
        form = FlagForm()

    context['form'] = form

    return render_to_response('packages/flag.html', context)



# vim: set ts=4 sw=4 et:


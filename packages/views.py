from django import forms
from django.contrib import messages
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template import loader, Context, RequestContext
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template

from datetime import datetime
import string

from main.models import Package, PackageFile
from main.models import Arch, Repo, Signoff
from main.utils import make_choice
from mirrors.models import MirrorUrl
from .models import PackageRelation
from .utils import get_group_info, get_differences_info

def opensearch(request):
    if request.is_secure():
        domain = "https://%s" % request.META['HTTP_HOST']
    else:
        domain = "http://%s" % request.META['HTTP_HOST']

    return direct_to_template(request, 'packages/opensearch.xml',
            {'domain': domain},
            mimetype='application/opensearchdescription+xml')

@permission_required('main.change_package')
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
        pkg = get_object_or_404(Package,
                pkgname=name, repo__name__iexact=repo, arch__name=arch)
        return direct_to_template(request, 'packages/details.html', {'pkg': pkg, })
    else:
        return redirect("/packages/?arch=%s&repo=%s&q=%s" % (
            arch.lower(), repo.title(), name))

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
    pkgs = Package.objects.filter(packagegroup__name=name,
            arch__in=arches)
    pkgs = pkgs.order_by('pkgname')
    if len(pkgs) == 0:
        raise Http404
    context = {
        'groupname': name,
        'arch': arch,
        'packages': pkgs,
    }
    return direct_to_template(request, 'packages/group_details.html', context)

def getmaintainer(request, name, repo, arch):
    "Returns the maintainers as plaintext."

    pkg = get_object_or_404(Package,
        pkgname=name, repo__name__iexact=repo, arch__name=arch)
    names = [m.username for m in pkg.maintainers]

    return HttpResponse(str('\n'.join(names)), mimetype='text/plain')

class PackageSearchForm(forms.Form):
    repo = forms.ChoiceField(required=False)
    arch = forms.ChoiceField(required=False)
    q = forms.CharField(required=False)
    maintainer = forms.ChoiceField(required=False)
    last_update = forms.DateField(required=False, widget=AdminDateWidget(),
            label='Last Updated After')
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
        self.fields['repo'].choices = [('', 'All')] + make_choice(
                        [repo.name for repo in Repo.objects.all()])
        self.fields['arch'].choices = [('', 'All')] + make_choice(
                        [arch.name for arch in Arch.objects.all()])
        self.fields['q'].widget.attrs.update({"size": "30"})
        maints = User.objects.filter(is_active=True).order_by('username')
        self.fields['maintainer'].choices = \
                [('', 'All'), ('orphan', 'Orphan')] + \
                [(m.username, m.get_full_name()) for m in maints]

def search(request, page=None):
    current_query = '?'
    limit = 50
    packages = Package.objects.select_related('arch', 'repo')

    if request.GET:
        current_query += request.GET.urlencode()
        form = PackageSearchForm(data=request.GET)
        if form.is_valid():
            if form.cleaned_data['repo']:
                packages = packages.filter(
                        repo__name=form.cleaned_data['repo'])

            if form.cleaned_data['arch']:
                packages = packages.filter(
                        arch__name=form.cleaned_data['arch'])

            if form.cleaned_data['maintainer'] == 'orphan':
                inner_q = PackageRelation.objects.all().values('pkgbase')
                packages = packages.exclude(pkgbase__in=inner_q)
            elif form.cleaned_data['maintainer']:
                inner_q = PackageRelation.objects.filter(user__username=form.cleaned_data['maintainer']).values('pkgbase')
                packages = packages.filter(pkgbase__in=inner_q)

            if form.cleaned_data['flagged'] == 'Flagged':
                packages=packages.filter(flag_date__isnull=False)
            elif form.cleaned_data['flagged'] == 'Not Flagged':
                packages = packages.filter(flag_date__isnull=True)

            if form.cleaned_data['q']:
                query = form.cleaned_data['q']
                q = Q(pkgname__icontains=query) | Q(pkgdesc__icontains=query)
                packages = packages.filter(q)
            if form.cleaned_data['last_update']:
                lu = form.cleaned_data['last_update']
                packages = packages.filter(last_update__gte=
                        datetime(lu.year, lu.month, lu.day, 0, 0))
            limit = form.cleaned_data['limit']
    else:
        form = PackageSearchForm()

    page_dict = {'search_form': form,
            'current_query': current_query
            }
    if packages.count() == 1:
        return redirect(packages[0])

    allowed_sort = ["arch", "repo", "pkgname", "last_update", "flag_date"]
    allowed_sort += ["-" + s for s in allowed_sort]
    sort = request.GET.get('sort', None)
    # TODO: sorting by multiple fields makes using a DB index much harder
    if sort in allowed_sort:
        packages = packages.order_by(
                request.GET['sort'], 'repo', 'arch', 'pkgname')
        page_dict['sort'] = sort
    else:
        packages = packages.order_by('pkgname')

    return list_detail.object_list(request, packages,
            template_name="packages/search.html",
            page=page,
            paginate_by=limit,
            template_object_name="package",
            extra_context=page_dict)

@vary_on_headers('X-Requested-With')
def files(request, name='', repo='', arch=''):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('path')
    template = 'packages/files.html'
    if request.is_ajax():
        template = 'packages/files-list.html'
    return direct_to_template(request, template,
            {'pkg':pkg, 'files':fileslist})

@permission_required('main.change_package')
def unflag(request, name='', repo='', arch=''):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    pkg.flag_date = None
    pkg.save()
    return redirect(pkg)

@permission_required('main.change_package')
@never_cache
def signoffs(request):
    packages = Package.objects.select_related('arch', 'repo', 'signoffs').filter(repo__testing=True).order_by("pkgname")
    package_list = []

    q_pkgname = Package.objects.filter(repo__testing=True).values('pkgname').distinct().query
    package_repos = Package.objects.values('pkgname', 'repo__name').exclude(repo__testing=True).filter(pkgname__in=q_pkgname)
    pkgtorepo = dict()
    for pr in package_repos:
        pkgtorepo[pr['pkgname']] = pr['repo__name']

    for package in packages:
        if package.pkgname in pkgtorepo:
            repo = pkgtorepo[package.pkgname]
        else:
            repo = "Unknown"
        package_list.append((package, repo))
    return direct_to_template(request, 'packages/signoffs.html',
            {'packages': package_list})

@permission_required('main.change_package')
@never_cache
def signoff_package(request, arch, pkgname):
    pkg = get_object_or_404(Package,
            arch__name=arch,
            pkgname=pkgname,
            repo__testing=True)

    signoff, created = Signoff.objects.get_or_create(
            pkg=pkg,
            pkgver=pkg.pkgver,
            pkgrel=pkg.pkgrel,
            packager=request.user)

    if request.is_ajax():
        data = {
            'created': created,
            'approved': pkg.approved_for_signoff(),
            'user': str(request.user),
        }
        return HttpResponse(simplejson.dumps(data),
                mimetype='application/json')

    return redirect('package-signoffs')

def flaghelp(request):
    return direct_to_template(request, 'packages/flaghelp.html')

class FlagForm(forms.Form):
    email = forms.EmailField(label='* E-mail Address')
    usermessage = forms.CharField(label='Message To Dev',
            widget=forms.Textarea, required=False)
    # The field below is used to filter out bots that blindly fill out all input elements
    website = forms.CharField(label='',
            widget=forms.TextInput(attrs={'style': 'display:none;'}),
            required=False)

@never_cache
def flag(request, name='', repo='', arch=''):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    context = {'pkg': pkg}
    if pkg.flag_date is not None:
        # already flagged. do nothing.
        return direct_to_template(request, 'packages/flagged.html', context)

    if request.POST:
        form = FlagForm(request.POST)
        if form.is_valid() and form.cleaned_data['website'] == '':
            # find all packages from (hopefully) the same PKGBUILD
            pkgs = Package.objects.filter(
                    pkgbase=pkg.pkgbase, repo__testing=pkg.repo.testing)
            pkgs.update(flag_date=datetime.now())

            maints = pkg.maintainers
            if not maints:
                toemail = settings.NOTIFICATIONS
                subject = 'Orphan %s package [%s] marked out-of-date' % \
                        (pkg.repo.name, pkg.pkgname)
            else:
                toemail = []
                subject = '%s package [%s] marked out-of-date' % \
                        (pkg.repo.name, pkg.pkgname)
                for maint in maints:
                    if maint.get_profile().notify == True:
                        toemail.append(maint.email)

            if toemail:
                # send notification email to the maintainer
                t = loader.get_template('packages/outofdate.txt')
                c = Context({
                    'email': form.cleaned_data['email'],
                    'message': form.cleaned_data['usermessage'],
                    'pkg': pkg,
                    'weburl': pkg.get_full_url(),
                })
                send_mail(subject,
                        t.render(c),
                        'Arch Website Notification <nobody@archlinux.org>',
                        toemail,
                        fail_silently=True)

            context['confirmed'] = True
    else:
        form = FlagForm()

    context['form'] = form

    return direct_to_template(request, 'packages/flag.html', context)

def download(request, name='', repo='', arch=''):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    mirrorurl = MirrorUrl.objects.filter(mirror__country='Any',
            mirror__public=True, mirror__active=True,
            protocol__protocol__iexact='HTTP')[0]
    arch = pkg.arch.name
    if pkg.arch.agnostic:
        # grab the first non-any arch to fake the download path
        arch = Arch.objects.exclude(agnostic=True)[0].name
    details = {
        'host': mirrorurl.url,
        'arch': arch,
        'repo': pkg.repo.name.lower(),
        'file': pkg.filename,
    }
    url = string.Template('${host}${repo}/os/${arch}/${file}').substitute(details)
    return redirect(url)

def arch_differences(request):
    # TODO: we have some hardcoded magic here with respect to the arches.
    arch_a = Arch.objects.get(name='i686')
    arch_b = Arch.objects.get(name='x86_64')
    differences = get_differences_info(arch_a, arch_b)
    context = {
            'arch_a': arch_a,
            'arch_b': arch_b,
            'differences': differences,
    }
    return direct_to_template(request, 'packages/differences.html', context)

# vim: set ts=4 sw=4 et:

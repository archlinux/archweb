from django import forms
from django.contrib import messages
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import (get_object_or_404, get_list_or_404,
        redirect, render)
from django.template import loader, Context
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template

from datetime import datetime
from operator import attrgetter
from string import Template
from urllib import urlencode

from main.models import Package, PackageFile, Arch, Repo
from main.utils import make_choice
from mirrors.models import MirrorUrl
from .models import PackageRelation, PackageGroup, SignoffSpecification, Signoff
from .utils import (get_group_info, get_differences_info,
        get_wrong_permissions, get_signoff_groups, approved_by_signoffs)

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

def coerce_limit_value(value):
    if not value:
        return None
    if value == 'all':
        # negative value indicates show all results
        return -1
    value = int(value)
    if value < 0:
        raise ValueError
    return value

class LimitTypedChoiceField(forms.TypedChoiceField):
    def valid_value(self, value):
        try:
            coerce_limit_value(value)
            return True
        except (ValueError, TypeError):
            return False

class PackageSearchForm(forms.Form):
    repo = forms.MultipleChoiceField(required=False)
    arch = forms.MultipleChoiceField(required=False)
    name = forms.CharField(required=False)
    desc = forms.CharField(required=False)
    q = forms.CharField(required=False)
    maintainer = forms.ChoiceField(required=False)
    packager = forms.ChoiceField(required=False)
    last_update = forms.DateField(required=False, widget=AdminDateWidget(),
            label='Last Updated After')
    flagged = forms.ChoiceField(
            choices=[('', 'All')] + make_choice(['Flagged', 'Not Flagged']),
            required=False)
    signed = forms.ChoiceField(
            choices=[('', 'All')] + make_choice(['Signed', 'Unsigned']),
            required=False)
    limit = LimitTypedChoiceField(
            choices=make_choice([50, 100, 250]) + [('all', 'All')],
            coerce=coerce_limit_value,
            required=False,
            initial=50)

    def __init__(self, *args, **kwargs):
        super(PackageSearchForm, self).__init__(*args, **kwargs)
        self.fields['repo'].choices = make_choice(
                        [repo.name for repo in Repo.objects.all()])
        self.fields['arch'].choices = make_choice(
                        [arch.name for arch in Arch.objects.all()])
        self.fields['q'].widget.attrs.update({"size": "30"})
        maints = User.objects.filter(is_active=True).order_by('username')
        self.fields['maintainer'].choices = \
                [('', 'All'), ('orphan', 'Orphan')] + \
                [(m.username, m.get_full_name()) for m in maints]
        self.fields['packager'].choices = \
                [('', 'All'), ('unknown', 'Unknown')] + \
                [(m.username, m.get_full_name()) for m in maints]

def search(request, page=None):
    limit = 50
    packages = Package.objects.normal()

    if request.GET:
        form = PackageSearchForm(data=request.GET)
        if form.is_valid():
            if form.cleaned_data['repo']:
                packages = packages.filter(
                        repo__name__in=form.cleaned_data['repo'])

            if form.cleaned_data['arch']:
                packages = packages.filter(
                        arch__name__in=form.cleaned_data['arch'])

            if form.cleaned_data['maintainer'] == 'orphan':
                inner_q = PackageRelation.objects.all().values('pkgbase')
                packages = packages.exclude(pkgbase__in=inner_q)
            elif form.cleaned_data['maintainer']:
                inner_q = PackageRelation.objects.filter(
                        user__username=form.cleaned_data['maintainer']).values('pkgbase')
                packages = packages.filter(pkgbase__in=inner_q)

            if form.cleaned_data['packager'] == 'unknown':
                packages = packages.filter(packager__isnull=True)
            elif form.cleaned_data['packager']:
                packages = packages.filter(
                        packager__username=form.cleaned_data['packager'])

            if form.cleaned_data['flagged'] == 'Flagged':
                packages = packages.filter(flag_date__isnull=False)
            elif form.cleaned_data['flagged'] == 'Not Flagged':
                packages = packages.filter(flag_date__isnull=True)

            if form.cleaned_data['signed'] == 'Signed':
                packages = packages.filter(pgp_signature__isnull=False)
            elif form.cleaned_data['signed'] == 'Unsigned':
                packages = packages.filter(pgp_signature__isnull=True)

            if form.cleaned_data['last_update']:
                lu = form.cleaned_data['last_update']
                packages = packages.filter(last_update__gte=
                        datetime(lu.year, lu.month, lu.day, 0, 0))

            if form.cleaned_data['name']:
                name = form.cleaned_data['name']
                packages = packages.filter(pkgname__icontains=name)

            if form.cleaned_data['desc']:
                desc = form.cleaned_data['desc']
                packages = packages.filter(pkgdesc__icontains=desc)

            if form.cleaned_data['q']:
                query = form.cleaned_data['q']
                q = Q(pkgname__icontains=query) | Q(pkgdesc__icontains=query)
                packages = packages.filter(q)

            asked_limit = form.cleaned_data['limit']
            if asked_limit and asked_limit < 0:
                limit = None
            elif asked_limit:
                limit = asked_limit
        else:
            # Form had errors, don't return any results, just the busted form
            packages = Package.objects.none()
    else:
        form = PackageSearchForm()

    current_query = request.GET.urlencode()
    page_dict = {
            'search_form': form,
            'current_query': current_query
    }
    allowed_sort = ["arch", "repo", "pkgname", "pkgbase",
            "compressed_size", "installed_size",
            "build_date", "last_update", "flag_date"]
    allowed_sort += ["-" + s for s in allowed_sort]
    sort = request.GET.get('sort', None)
    if sort in allowed_sort:
        packages = packages.order_by(sort)
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
def files(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    fileslist = PackageFile.objects.filter(pkg=pkg).order_by('directory', 'filename')
    context = {
        'pkg': pkg,
        'files': fileslist,
    }
    template = 'packages/files.html'
    if request.is_ajax():
        template = 'packages/files-list.html'
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

@permission_required('main.change_package')
def unflag(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    pkg.flag_date = None
    pkg.save()
    return redirect(pkg)

@permission_required('main.change_package')
def unflag_all(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    # find all packages from (hopefully) the same PKGBUILD
    pkgs = Package.objects.filter(pkgbase=pkg.pkgbase,
            repo__testing=pkg.repo.testing, repo__staging=pkg.repo.staging)
    pkgs.update(flag_date=None)
    return redirect(pkg)

@permission_required('main.change_package')
@never_cache
def signoffs(request):
    signoff_groups = sorted(get_signoff_groups(), key=attrgetter('pkgbase'))
    for group in signoff_groups:
        group.user = request.user

    context = {
        'signoff_groups': signoff_groups,
        'arches': Arch.objects.all(),
    }
    return direct_to_template(request, 'packages/signoffs.html', context)

@permission_required('main.change_package')
@never_cache
def signoff_package(request, name, repo, arch, revoke=False):
    packages = get_list_or_404(Package, pkgbase=name,
            arch__name=arch, repo__name__iexact=repo, repo__testing=True)
    package = packages[0]

    spec = SignoffSpecification.objects.get_or_default_from_package(package)

    if revoke:
        try:
            signoff = Signoff.objects.get_from_package(
                    package, request.user, False)
        except Signoff.DoesNotExist:
            raise Http404
        signoff.revoked = datetime.utcnow()
        signoff.save()
        created = False
    else:
        # ensure we should even be accepting signoffs
        if spec.known_bad or not spec.enabled:
            return render(request, '403.html', status=403)
        signoff, created = Signoff.objects.get_or_create_from_package(
                package, request.user)

    all_signoffs = Signoff.objects.for_package(package)

    if request.is_ajax():
        data = {
            'created': created,
            'revoked': bool(signoff.revoked),
            'approved': approved_by_signoffs(all_signoffs, spec),
            'required': spec.required,
            'enabled': spec.enabled,
            'known_bad': spec.known_bad,
            'user': str(request.user),
        }
        return HttpResponse(simplejson.dumps(data, ensure_ascii=False),
                mimetype='application/json')

    return redirect('package-signoffs')

class SignoffOptionsForm(forms.ModelForm):
    class Meta:
        model = SignoffSpecification
        fields = ('required', 'enabled', 'known_bad', 'comments')

@permission_required('main.change_package')
@never_cache
def signoff_options(request, name, repo, arch):
    packages = get_list_or_404(Package, pkgbase=name,
            arch__name=arch, repo__name__iexact=repo, repo__testing=True)
    package = packages[0]

    if request.user != package.packager and \
            request.user not in package.maintainers:
        return render(request, '403.html', status=403)

    try:
        spec = SignoffSpecification.objects.get_from_package(package)
    except SignoffSpecification.DoesNotExist:
        # create a fake one, but don't save it just yet
        spec = SignoffSpecification(pkgbase=package.pkgbase,
                pkgver=package.pkgver, pkgrel=package.pkgrel,
                epoch=package.epoch, arch=package.arch, repo=package.repo)
        spec.user = request.user

    if request.POST:
        form = SignoffOptionsForm(request.POST, instance=spec)
        if form.is_valid():
            form.save()
            return redirect('package-signoffs')
    else:
        form = SignoffOptionsForm(instance=spec)

    context = {
        'packages': packages,
        'package': package,
        'form': form,
    }
    return direct_to_template(request, 'packages/signoff_options.html', context)

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
def flag(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    if pkg.flag_date is not None:
        # already flagged. do nothing.
        return direct_to_template(request, 'packages/flagged.html', {'pkg': pkg})
    # find all packages from (hopefully) the same PKGBUILD
    pkgs = Package.objects.normal().filter(
            pkgbase=pkg.pkgbase, flag_date__isnull=True,
            repo__testing=pkg.repo.testing,
            repo__staging=pkg.repo.staging).order_by(
            'pkgname', 'repo__name', 'arch__name')

    if request.POST:
        form = FlagForm(request.POST)
        if form.is_valid() and form.cleaned_data['website'] == '':
            # save the package list for later use
            flagged_pkgs = list(pkgs)
            pkgs.update(flag_date=datetime.utcnow())

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
                # send notification email to the maintainers
                t = loader.get_template('packages/outofdate.txt')
                c = Context({
                    'email': form.cleaned_data['email'],
                    'message': form.cleaned_data['usermessage'],
                    'pkg': pkg,
                    'packages': flagged_pkgs,
                })
                send_mail(subject,
                        t.render(c),
                        'Arch Website Notification <nobody@archlinux.org>',
                        toemail,
                        fail_silently=True)

            return redirect('package-flag-confirmed', name=name, repo=repo,
                    arch=arch)
    else:
        form = FlagForm()

    context = {
        'package': pkg,
        'packages': pkgs,
        'form': form
    }
    return direct_to_template(request, 'packages/flag.html', context)

def flag_confirmed(request, name, repo, arch):
    pkg = get_object_or_404(Package,
            pkgname=name, repo__name__iexact=repo, arch__name=arch)
    pkgs = Package.objects.normal().filter(
            pkgbase=pkg.pkgbase, flag_date=pkg.flag_date,
            repo__testing=pkg.repo.testing,
            repo__staging=pkg.repo.staging).order_by(
            'pkgname', 'repo__name', 'arch__name')

    context = {'package': pkg, 'packages': pkgs}

    return direct_to_template(request, 'packages/flag_confirmed.html', context)

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
    context = {
            'arch_a': arch_a,
            'arch_b': arch_b,
            'differences': differences,
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

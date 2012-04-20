from datetime import date, datetime, timedelta
import operator
import pytz
import random
from string import ascii_letters, digits
import time

from django import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import \
        login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template import loader, Context
from django.template.defaultfilters import filesizeformat
from django.views.decorators.cache import never_cache
from django.views.generic.simple import direct_to_template
from django.utils.http import http_date

from .models import UserProfile
from main.models import Package, PackageDepend, PackageFile, TodolistPkg
from main.models import Arch, Repo
from main.utils import utc_now
from packages.models import PackageRelation
from packages.utils import get_signoff_groups
from todolists.utils import get_annotated_todolists
from .utils import get_annotated_maintainers, UserFinder


@login_required
def index(request):
    '''the developer dashboard'''
    if(request.user.is_authenticated()):
        inner_q = PackageRelation.objects.filter(user=request.user)
    else:
        inner_q = PackageRelation.objects.none()
    inner_q = inner_q.values('pkgbase')

    flagged = Package.objects.normal().filter(
            flag_date__isnull=False, pkgbase__in=inner_q).order_by('pkgname')

    todopkgs = TodolistPkg.objects.select_related(
            'pkg', 'pkg__arch', 'pkg__repo').filter(complete=False)
    todopkgs = todopkgs.filter(pkg__pkgbase__in=inner_q).order_by(
            'list__name', 'pkg__pkgname')

    todolists = get_annotated_todolists()
    todolists = [todolist for todolist in todolists if todolist.incomplete_count > 0]

    signoffs = sorted(get_signoff_groups(user=request.user),
            key=operator.attrgetter('pkgbase'))

    maintainers = get_annotated_maintainers()

    maintained = PackageRelation.objects.filter(
            type=PackageRelation.MAINTAINER).values('pkgbase')
    total_orphans = Package.objects.exclude(pkgbase__in=maintained).count()
    total_flagged_orphans = Package.objects.filter(
            flag_date__isnull=False).exclude(pkgbase__in=maintained).count()
    total_updated = Package.objects.filter(packager__isnull=True).count()
    orphan = {
            'package_count': total_orphans,
            'flagged_count': total_flagged_orphans,
            'updated_count': total_updated,
    }

    page_dict = {
            'todos': todolists,
            'repos': Repo.objects.all(),
            'arches': Arch.objects.all(),
            'maintainers': maintainers,
            'orphan': orphan,
            'flagged' : flagged,
            'todopkgs' : todopkgs,
            'signoffs': signoffs
    }

    return direct_to_template(request, 'devel/index.html', page_dict)

@login_required
def clock(request):
    devs = User.objects.filter(is_active=True).order_by(
            'first_name', 'last_name').select_related('userprofile')

    now = utc_now()
    page_dict = {
            'developers': devs,
            'utc_now': now,
    }

    response = direct_to_template(request, 'devel/clock.html', page_dict)
    if not response.has_header('Expires'):
        expire_time = now.replace(second=0, microsecond=0)
        expire_time += timedelta(minutes=1)
        expire_time = time.mktime(expire_time.timetuple())
        response['Expires'] = http_date(expire_time)
    return response

class ProfileForm(forms.Form):
    email = forms.EmailField(label='Private email (not shown publicly):',
            help_text="Used for out-of-date notifications, etc.")
    passwd1 = forms.CharField(label='New Password', required=False,
            widget=forms.PasswordInput)
    passwd2 = forms.CharField(label='Confirm Password', required=False,
            widget=forms.PasswordInput)

    def clean(self):
        if self.cleaned_data['passwd1'] != self.cleaned_data['passwd2']:
            raise forms.ValidationError('Passwords do not match.')
        return self.cleaned_data

class UserProfileForm(forms.ModelForm):
    def clean_pgp_key(self):
        data = self.cleaned_data['pgp_key']
        # strip 0x prefix if provided; store uppercase
        if data.startswith('0x'):
            data = data[2:]
        return data.upper()

    class Meta:
        model = UserProfile
        exclude = ('allowed_repos', 'user', 'latin_name')

@login_required
@never_cache
def change_profile(request):
    if request.POST:
        form = ProfileForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.get_profile())
        if form.is_valid() and profile_form.is_valid():
            request.user.email = form.cleaned_data['email']
            if form.cleaned_data['passwd1']:
                request.user.set_password(form.cleaned_data['passwd1'])
            request.user.save()
            profile_form.save()
            return HttpResponseRedirect('/devel/')
    else:
        form = ProfileForm(initial={'email': request.user.email})
        profile_form = UserProfileForm(instance=request.user.get_profile())
    return direct_to_template(request, 'devel/profile.html',
            {'form': form, 'profile_form': profile_form})

@login_required
def report(request, report_name, username=None):
    title = 'Developer Report'
    packages = Package.objects.normal()
    names = attrs = user = None

    if username:
        user = get_object_or_404(User, username=username, is_active=True)
        maintained = PackageRelation.objects.filter(user=user,
                type=PackageRelation.MAINTAINER).values('pkgbase')
        packages = packages.filter(pkgbase__in=maintained)

    maints = User.objects.filter(id__in=PackageRelation.objects.filter(
        type=PackageRelation.MAINTAINER).values('user'))

    if report_name == 'old':
        title = 'Packages last built more than one year ago'
        cutoff = utc_now() - timedelta(days=365)
        packages = packages.filter(
                build_date__lt=cutoff).order_by('build_date')
    elif report_name == 'long-out-of-date':
        title = 'Packages marked out-of-date more than 90 days ago'
        cutoff = utc_now() - timedelta(days=90)
        packages = packages.filter(
                flag_date__lt=cutoff).order_by('flag_date')
    elif report_name == 'big':
        title = 'Packages with compressed size > 50 MiB'
        cutoff = 50 * 1024 * 1024
        packages = packages.filter(
                compressed_size__gte=cutoff).order_by('-compressed_size')
        names = [ 'Compressed Size', 'Installed Size' ]
        attrs = [ 'compressed_size_pretty', 'installed_size_pretty' ]
        # Format the compressed and installed sizes with MB/GB/etc suffixes
        for package in packages:
            package.compressed_size_pretty = filesizeformat(
                package.compressed_size)
            package.installed_size_pretty = filesizeformat(
                package.installed_size)
    elif report_name == 'badcompression':
        title = 'Packages that have little need for compression'
        cutoff = 0.90 * F('installed_size')
        packages = packages.filter(compressed_size__gt=0, installed_size__gt=0,
                compressed_size__gte=cutoff).order_by('-compressed_size')
        names = [ 'Compressed Size', 'Installed Size', 'Ratio', 'Type' ]
        attrs = [ 'compressed_size_pretty', 'installed_size_pretty',
                'ratio', 'compress_type' ]
        # Format the compressed and installed sizes with MB/GB/etc suffixes
        for package in packages:
            package.compressed_size_pretty = filesizeformat(
                package.compressed_size)
            package.installed_size_pretty = filesizeformat(
                package.installed_size)
            ratio = package.compressed_size / float(package.installed_size)
            package.ratio = '%.2f' % ratio
            package.compress_type = package.filename.split('.')[-1]
    elif report_name == 'uncompressed-man':
        title = 'Packages with uncompressed manpages'
        # checking for all '.0'...'.9' + '.n' extensions
        bad_files = PackageFile.objects.filter(is_directory=False,
                directory__contains='/man/',
                filename__regex=r'\.[0-9n]').exclude(
                filename__endswith='.gz').exclude(
                filename__endswith='.xz').exclude(
                filename__endswith='.bz2').exclude(
                filename__endswith='.html')
        if username:
            pkg_ids = set(packages.values_list('id', flat=True))
            bad_files = bad_files.filter(pkg__in=pkg_ids)
        bad_files = bad_files.values_list('pkg_id', flat=True).distinct()
        packages = packages.filter(id__in=set(bad_files))
    elif report_name == 'uncompressed-info':
        title = 'Packages with uncompressed infopages'
        # we don't worry about looking for '*.info-1', etc., given that an
        # uncompressed root page probably exists in the package anyway
        bad_files = PackageFile.objects.filter(is_directory=False,
                directory__endswith='/info/', filename__endswith='.info')
        if username:
            pkg_ids = set(packages.values_list('id', flat=True))
            bad_files = bad_files.filter(pkg__in=pkg_ids)
        bad_files = bad_files.values_list('pkg_id', flat=True).distinct()
        packages = packages.filter(id__in=set(bad_files))
    elif report_name == 'unneeded-orphans':
        title = 'Orphan packages required by no other packages'
        owned = PackageRelation.objects.all().values('pkgbase')
        required = PackageDepend.objects.all().values('depname')
        # The two separate calls to exclude is required to do the right thing
        packages = packages.exclude(pkgbase__in=owned).exclude(
                pkgname__in=required)
    elif report_name == 'mismatched-signature':
        title = 'Packages with mismatched signatures'
        names = [ 'Signature Date', 'Signed By', 'Packager' ]
        attrs = [ 'sig_date', 'sig_by', 'packager' ]
        cutoff = timedelta(hours=24)
        finder = UserFinder()
        filtered = []
        packages = packages.filter(pgp_signature__isnull=False)
        for package in packages:
            sig_date = package.signature.datetime.replace(tzinfo=pytz.utc)
            package.sig_date = sig_date.date()
            key_id = package.signature.key_id
            signer = finder.find_by_pgp_key(key_id)
            package.sig_by = signer or key_id
            if signer is None or signer.id != package.packager_id:
                filtered.append(package)
            elif sig_date > package.build_date + cutoff:
                filtered.append(package)
        packages = filtered
    else:
        raise Http404

    context = {
        'all_maintainers': maints,
        'title': title,
        'maintainer': user,
        'packages': packages,
        'column_names': names,
        'column_attrs': attrs,
    }
    return direct_to_template(request, 'devel/packages.html', context)


class NewUserForm(forms.ModelForm):
    username = forms.CharField(max_length=30)
    private_email = forms.EmailField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    groups = forms.ModelMultipleChoiceField(required=False,
            queryset=Group.objects.all())

    class Meta:
        model = UserProfile
        exclude = ('picture', 'user')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        # Hack ourself so certain fields appear first. self.fields is a
        # SortedDict object where we can manipulate the keyOrder list.
        order = self.fields.keyOrder
        keys = ('username', 'private_email', 'first_name', 'last_name')
        for key in reversed(keys):
            order.remove(key)
            order.insert(0, key)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                    "A user with that username already exists.")
        return username

    def save(self, commit=True):
        profile = super(NewUserForm, self).save(False)
        pwletters = ascii_letters + digits
        password = ''.join([random.choice(pwletters) for _ in xrange(8)])
        user = User.objects.create_user(username=self.cleaned_data['username'],
                email=self.cleaned_data['private_email'], password=password)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        # sucks that the MRM.add() method can't take a list directly... we have
        # to resort to dirty * magic.
        user.groups.add(*self.cleaned_data['groups'])
        profile.user = user
        if commit:
            profile.save()
            self.save_m2m()

        template = loader.get_template('devel/new_account.txt')
        ctx = Context({
            'site': Site.objects.get_current(),
            'user': user,
            'password': password,
        })

        send_mail("Your new archweb account",
                template.render(ctx),
                'Arch Website Notification <nobody@archlinux.org>',
                [user.email],
                fail_silently=False)

def log_addition(request, obj):
    """Cribbed from ModelAdmin.log_addition."""
    from django.contrib.admin.models import LogEntry, ADDITION
    from django.contrib.contenttypes.models import ContentType
    from django.utils.encoding import force_unicode
    LogEntry.objects.log_action(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(obj).pk,
        object_id       = obj.pk,
        object_repr     = force_unicode(obj),
        action_flag     = ADDITION,
        change_message  = "Added via Create New User form."
    )

@permission_required('auth.add_user')
@never_cache
def new_user_form(request):
    if request.POST:
        form = NewUserForm(request.POST)
        if form.is_valid():
            @transaction.commit_on_success
            def inner_save():
                form.save()
                log_addition(request, form.instance.user)
            inner_save()
            return HttpResponseRedirect('/admin/auth/user/%d/' % \
                    form.instance.user.id)
    else:
        form = NewUserForm()

    context = {
        'description': '''A new user will be created with the
            following properties in their profile. A random password will be
            generated and the user will be e-mailed with their account details
            n plaintext.''',
        'form': form,
        'title': 'Create User',
        'submit_text': 'Create User'
    }
    return direct_to_template(request, 'general_form.html', context)

@user_passes_test(lambda u: u.is_superuser)
def admin_log(request, username=None):
    user = None
    if username:
        user = get_object_or_404(User, username=username)
    context = {
        'title': "Admin Action Log",
        'log_user':  user,
    }
    return direct_to_template(request, 'devel/admin_log.html', context)

# vim: set ts=4 sw=4 et:

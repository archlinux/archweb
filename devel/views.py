from django import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import \
        login_required, permission_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template import loader, Context
from django.views.decorators.cache import never_cache
from django.views.generic.simple import direct_to_template

from main.models import Package, Todolist, TodolistPkg
from main.models import Arch, Repo
from main.models import UserProfile
from packages.models import PackageRelation
from .utils import get_annotated_maintainers

import datetime
import pytz
import random
from string import ascii_letters, digits

@login_required
@never_cache
def index(request):
    '''the Developer dashboard'''
    inner_q = PackageRelation.objects.filter(user=request.user).values('pkgbase')
    flagged = Package.objects.select_related('arch', 'repo').filter(
            flag_date__isnull=False, pkgbase__in=inner_q).order_by('pkgname')

    todopkgs = TodolistPkg.objects.select_related(
            'pkg', 'pkg__arch', 'pkg__repo').filter(complete=False)
    todopkgs = todopkgs.filter(pkg__pkgbase__in=inner_q).order_by(
            'list__name', 'pkg__pkgname')

    maintainers = get_annotated_maintainers()

    maintained = PackageRelation.objects.filter(
            type=PackageRelation.MAINTAINER).values('pkgbase')
    total_orphans = Package.objects.exclude(pkgbase__in=maintained).count()
    total_flagged_orphans = Package.objects.filter(
            flag_date__isnull=False).exclude(pkgbase__in=maintained).count()
    orphan = {
            'package_count': total_orphans,
            'flagged_count': total_flagged_orphans,
    }

    page_dict = {
            'todos': Todolist.objects.incomplete().order_by('-date_added'),
            'repos': Repo.objects.all(),
            'arches': Arch.objects.all(),
            'maintainers': maintainers,
            'orphan': orphan,
            'flagged' : flagged,
            'todopkgs' : todopkgs,
    }

    return direct_to_template(request, 'devel/index.html', page_dict)

@login_required
@never_cache
def clock(request):
    devs = User.objects.filter(is_active=True).order_by(
            'username').select_related('userprofile')

    # now annotate each dev object with their current time
    now = datetime.datetime.now()
    utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    for dev in devs:
        # Work around https://bugs.launchpad.net/pytz/+bug/718673
        timezone = str(dev.userprofile.time_zone)
        tz = pytz.timezone(timezone)
        dev.current_time = utc_now.astimezone(tz)

    page_dict = {
            'developers': devs,
            'now': now,
            'utc_now': utc_now,
    }

    return direct_to_template(request, 'devel/clock.html', page_dict)

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
    class Meta:
        model = UserProfile
        exclude = ['allowed_repos', 'user']

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
        password = ''.join([random.choice(pwletters) for i in xrange(8)])
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

        t = loader.get_template('devel/new_account.txt')
        c = Context({
            'site': Site.objects.get_current(),
            'user': user,
            'password': password,
        })

        send_mail("Your new archweb account",
                t.render(c),
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
@never_cache
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

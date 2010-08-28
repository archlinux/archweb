from django import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache

from main.models import Package, Todolist, TodolistPkg
from main.models import Arch, Repo
from main.models import UserProfile
from main.models import Mirror
from packages.models import PackageRelation

import random
from string import ascii_letters, digits

@login_required
@never_cache
def index(request):
    '''the Developer dashboard'''
    inner_q = PackageRelation.objects.filter(user=request.user).values('pkgbase')
    flagged = Package.objects.select_related('arch', 'repo').filter(flag_date__isnull=False)
    flagged = flagged.filter(pkgbase__in=inner_q).order_by('pkgname')

    todopkgs = TodolistPkg.objects.select_related(
            'pkg', 'pkg__arch', 'pkg__repo').filter(complete=False)
    todopkgs = todopkgs.filter(pkg__pkgbase__in=inner_q).order_by(
            'list__name', 'pkg__pkgname')
    maintainers = User.objects.filter(is_active=True).order_by(
            'first_name', 'last_name')

    page_dict = {
            'todos': Todolist.objects.incomplete().order_by('-date_added'),
            'repos': Repo.objects.all(),
            'arches': Arch.objects.all(),
            'maintainers': maintainers,
            'flagged' : flagged,
            'todopkgs' : todopkgs,
         }

    return render_to_response('devel/index.html',
        RequestContext(request, page_dict))

@login_required
def change_notify(request):
    maint = User.objects.get(username=request.user.username)
    notify = request.POST.get('notify', 'no')
    prof = maint.get_profile()
    prof.notify = (notify == 'yes')
    prof.save()
    return HttpResponseRedirect('/devel/')

class ProfileForm(forms.Form):
    email = forms.EmailField(label='E-mail Address')
    passwd1 = forms.CharField(label='New Password', required=False,
            widget=forms.PasswordInput)
    passwd2 = forms.CharField(label='Confirm Password', required=False,
            widget=forms.PasswordInput)

    def clean(self):
        if self.cleaned_data['passwd1'] != self.cleaned_data['passwd2']:
            raise forms.ValidationError('Passwords do not match.')
        return self.cleaned_data

@login_required
@never_cache
def change_profile(request):
    if request.POST:
        form = ProfileForm(request.POST)
        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            if form.cleaned_data['passwd1']:
                request.user.set_password(form.cleaned_data['passwd1'])
            request.user.save()
            return HttpResponseRedirect('/devel/')
    else:
        form = ProfileForm(initial={'email': request.user.email})
    return render_to_response('devel/profile.html',
            RequestContext(request, {'form': form}))

@login_required
def mirrorlist(request):
    mirrors = Mirror.objects.select_related().order_by('tier', 'country')
    return render_to_response('devel/mirrorlist.html',
            RequestContext(request, {'mirror_list': mirrors}))

class NewUserForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('picture', 'user')
    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    def save(self):
        profile = forms.ModelForm.save(self, False)
        pwletters = ascii_letters + digits
        pw = ''.join([random.choice(pwletters) for i in xrange(8)])
        user = User.objects.create_user(username=self.cleaned_data['username'],
                email=self.cleaned_data['email'], password=pw)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        profile.user = user
        profile.save()
        domain = Site.objects.get_current().domain

        send_mail("Your new archweb account",
                """You can now log into:
https://%s/login/
with these login details:
Username: %s
Password: %s""" % (domain, user.username, pw),
                'Arch Website Notification <nobody@archlinux.org>',
                [user.email],
                fail_silently=False)

@user_passes_test(lambda u: u.is_superuser)
@never_cache
def new_user_form(request):
    if request.POST:
        form = NewUserForm(request.POST)
        if form.is_valid():
            form.save()
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
    return render_to_response('general_form.html',
            RequestContext(request, context))

# vim: set ts=4 sw=4 et:

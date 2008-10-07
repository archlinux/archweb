from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import Package, Todolist
from archweb_dev.main.models import Arch, Repo
from archweb_dev.main.models import UserProfile, News, Donor, Mirror

def index(request):
    try:
        thismaint = User.objects.get(username=request.user.username)
    except User.DoesNotExist:
        # weird, we don't have a maintainer record for this logged-in user
        thismaint = None

    # get a list of incomplete package todo lists
    todos = Todolist.objects.get_incomplete()
    # get flagged-package stats for all maintainers
    stats = Package.objects.get_flag_stats()
    if thismaint:
        # get list of flagged packages for this maintainer
        pkgs = Package.objects.filter(
            maintainer=thismaint.id).filter(
                needupdate=True).order_by('repo', 'pkgname')
    else:
        pkgs = None

    arch_stats = []
    for xarch in Arch.objects.all():
        arch_stats.append({ 
            'name': xarch.name,
            'count': Package.objects.filter(arch=xarch).count(),
            'flagged': Package.objects.filter(arch=xarch).filter(
                needupdate=True).exclude(
                    repo__name__iexact='testing').count()
        })

    repo_stats = []
    for xrepo in Repo.objects.all():
        repo_stats.append({ 
            'name': xrepo.name,
            'count': Package.objects.filter(repo=xrepo).count(),
            'flagged': Package.objects.filter(
                repo=xrepo).filter(needupdate=True).count()
        })

    return render_response(
        request, 'devel/index.html',
        {'stats': stats, 'pkgs': pkgs, 'todos': todos, 'maint': thismaint, 
         'repos': repo_stats, 'arches': arch_stats})

#@is_maintainer
def change_notify(request):
    maint = User.objects.get(username=request.user.username)
    notify = request.POST.get('notify', 'no')
    try:
        maint.get_profile().notify = notify == 'yes'
    except UserProfile.DoesNotExist:
        UserProfile(user_id=maint.id ,notify=notify == 'yes').save()
    maint.get_profile().save()
    return HttpResponseRedirect('/devel/')

class ProfileForm(forms.Form):
    email = forms.EmailField('E-mail Address')
    passwd1 = forms.CharField('New Password', required=False,
            widget=forms.PasswordInput)
    passwd2 = forms.CharField('Confirm Password', required=False,
            widget=forms.PasswordInput)

    def clean(self):
        if ('passwd1' not in self.cleaned_data and
                'passwd2' not in self.cleaned_data):
            return self.cleaned_data
            
        if self.cleaned_data['passwd1'] != self.cleaned_data['passwd2']:
            raise forms.ValidationError('Passwords do not match')
        return self.cleaned_data

def change_profile(request):
    if request.POST:
        form = ProfileForm(request.POST)
        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            request.user.set_password(form.cleaned_data['passwd1'])
            request.user.save()
            return HttpResponseRedirect('/devel/')
    else:
        form = ProfileForm(initial={'email': request.user.email})
    return render_response(request, 'devel/profile.html', {'form': form})

def siteindex(request):
    # get the most recent 10 news items
    news  = News.objects.order_by('-postdate', '-id')[:10]
    pkgs  = Package.objects.exclude(repo__name__iexact='testing').order_by('-last_update')[:15]
    repos = Repo.objects.all()
    return render_response(
        request, 'devel/siteindex.html', 
        {'news_updates': news, 'pkg_updates': pkgs, 'repos': repos})

def denied(request):
    return render_response(request, 'devel/denied.html')

# vim: set ts=4 sw=4 et:


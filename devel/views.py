from django import forms
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext
from archweb_dev.main.models import Package, Todolist
from archweb_dev.main.models import Arch, Repo
from archweb_dev.main.models import UserProfile, News

def index(request):
    '''the Developer dashboard'''
    page_dict = {
            'todos': Todolist.objects.incomplete(),
            'repos': Repo.objects.all(), 'arches': Arch.objects.all(),
            'maintainers': [
                User(id=0, username="orphan", first_name="Orphans")
                ] + list(User.objects.filter(is_active=True).order_by('username'))
         }

    return render_to_response('devel/index.html',
        RequestContext(request, page_dict))

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
    return render_to_response('devel/profile.html',
            RequestContext(request, {'form': form}))

def siteindex(request):
    news  = News.objects.order_by('-postdate', '-id')[:10]
    pkgs  = Package.objects.exclude(repo__name__iexact='testing').order_by(
            '-last_update')[:15]
    repos = Repo.objects.all()
    return render_to_response('devel/siteindex.html', 
            RequestContext(request,
                {'news_updates': news, 'pkg_updates': pkgs, 'repos': repos}))

# vim: set ts=4 sw=4 et:


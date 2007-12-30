from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import validators
from archweb_dev.lib.utils import render_response
from archweb_dev.packages.models import Package, Repo
from archweb_dev.todolists.models import Todolist, TodolistPkg
from archweb_dev.settings import DATA_DIR
from archweb_dev.lib.utils import validate
from archweb_dev.devel.models import UserProfile
from archweb_dev.news.models import News
from archweb_dev.settings import DATA_DIR
from archweb_dev.devel.models import Donator, Mirror


@login_required
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
        pkgs = Package.objects.filter(maintainer=thismaint.id).filter(needupdate=True).order_by('repo', 'pkgname')
    else:
        pkgs = None

    repo_stats = []
    for repo in Repo.objects.all():
        repo_stats.append({ 
            'name': repo.name,
            'count': Package.objects.filter(repo__exact = repo).count(),
            'flagged': Package.objects.filter(repo__exact = repo).filter(needupdate=True).count()
        })

    return render_response(request, 'devel/index.html',
        {'stats':stats, 
         'pkgs':pkgs, 
         'todos':todos, 
         'maint':thismaint,
         'repos': repo_stats})

@login_required
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

@login_required
def change_profile(request):
    errors = {}
    if request.POST:
        passwd1, passwd2 = request.POST['passwd'], request.POST['passwd2']
        email = request.POST['email']
        # validate
        if passwd1 != passwd2:
            errors['password'] = ['  Passwords do not match.  ']
        validate(errors, 'Email', email, validators.isValidEmail, False, request)
        # apply changes
        if not errors:
            request.user.email = email
            if passwd1:
                request.user.set_password(passwd1)
            request.user.save()
            return HttpResponseRedirect('/devel/')
    return render_response(request, 'devel/profile.html', {'errors':errors,'email':request.user.email})

@login_required
def guide(request):
    return render_response(request, 'devel/pkgmaint_guide.txt', 
                           mimetype='text/plain')

def siteindex(request):
    # get the most recent 10 news items
    news  = News.objects.order_by('-postdate', '-id')[:10]
    pkgs  = Package.objects.exclude(repo__name__exact='Testing').order_by('-last_update')[:15]
    repos = Repo.objects.order_by('name')
    return render_response(request, 'devel/siteindex.html', {'news_updates':news,'pkg_updates':pkgs,'repos':repos})

def cvs(request):
    return render_response(request, 'devel/cvs.html')

def developers(request):
    devs = User.objects.order_by('username')
    return render_response(request, 'devel/developers.html', {'devs':devs})

def donate(request):
    donor_count = Donator.objects.count()
    splitval = donor_count / 4
    slice1 = Donator.objects.all()[:splitval]
    slice2 = Donator.objects.all()[(splitval):(splitval*2)]
    slice3 = Donator.objects.all()[(splitval*2):(donor_count-splitval)]
    slice4 = Donator.objects.all()[(donor_count-splitval):donor_count]
    return render_response(request, 'devel/donate.html',
        {'slice1':slice1,'slice2':slice2,'slice3':slice3,'slice4':slice4})

def download(request):
    mirrors = Mirror.objects.order_by('country', 'domain')
    return render_response(request, 'devel/download.html', {'mirrors':mirrors})

def projects(request):
    return render_response(request, 'devel/projects.html')

def robots(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", mimetype="text/plain")

def denied(request):
    return render_response(request, 'devel/denied.html')

# vim: set ts=4 sw=4 et:


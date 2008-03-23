from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import validators
from archweb_dev.main.utils import render_response, validate
from archweb_dev.main.models import Package, Todolist, TodolistPkg
from archweb_dev.main.models import UserProfile, News, Donor, Mirror
from django.http import HttpResponse
from django.template import Context, loader


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
    arch_stats = []
    for arch in Arch.objects.all():
        arch_stats.append({ 
            'name': arch.name,
            'count': Package.objects.filter(arch__exact = arch).count(),
            'flagged': Package.objects.filter(arch__exact = arch).filter(needupdate=True).count()
        })

    repo_stats = []
    for repo in Package.REPOS:
        repo_stats.append({ 
            'name': repo,
            'count': Package.objects.filter(repo = Package.REPOS[repo]).count(),
            'flagged': Package.objects.filter(Package.REPOS[repo]).filter(needupdate=True).count()
        })

    return render_response(
        request, 'devel/index.html',
        {'stats': stats, 'pkgs': pkgs, 'todos': todos, 'maint': thismaint, 
         'repos': repo_stats, 'archs': arch_stats})

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
    t = loader.get_template('devel/pkgmaint_guide.txt')
    c = Context()
    return HttpResponse(t.render(c), mimetype="text/plain")
    #return render_response(request, 'devel/pkgmaint_guide.txt',
    #                       mimetype='text/plain')

def siteindex(request):
    # get the most recent 10 news items
    news  = News.objects.order_by('-postdate', '-id')[:10]
    pkgs  = Package.objects.exclude(repo = Package.REPOS.testing).order_by('-last_update')[:15]
    repos = Package.REPOS
    return render_response(
        request, 'devel/siteindex.html', 
        {'news_updates': news, 'pkg_updates': pkgs, 'repos': repos})

def cvs(request):
    return render_response(request, 'devel/cvs.html')

def developers(request):
    devs = User.objects.filter(is_active=True).order_by('username')
    return render_response(request, 'devel/developers.html', {'devs':devs})

def donate(request):
    donor_count = Donor.objects.count()
    splitval = donor_count / 4
    slice1 = Donor.objects.all()[:splitval]
    slice2 = Donor.objects.all()[(splitval):(splitval*2)]
    slice3 = Donor.objects.all()[(splitval*2):(donor_count-splitval)]
    slice4 = Donor.objects.all()[(donor_count-splitval):donor_count]
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


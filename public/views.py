from django.http import HttpResponse
from archweb_dev.lib.utils import render_response
from django.contrib.auth.models import User
from archweb_dev.packages.models import Package, Repo
from archweb_dev.news.models import News
from archweb_dev.settings import DATA_DIR
from archweb_dev.public.models import Donator, Mirror

def index(request):
    # get the most recent 10 news items
    news  = News.objects.order_by('-postdate', '-id')[:10]
    pkgs  = Package.objects.exclude(repo__name__exact='Testing').order_by('-last_update')[:15]
    repos = Repo.objects.order_by('name')
    return render_response(request, 'public/index.html', {'news_updates':news,'pkg_updates':pkgs,'repos':repos})

def about(request):
    return render_response(request, 'public/about.html')

def art(request):
    return render_response(request, 'public/art.html')

def cvs(request):
    return render_response(request, 'public/cvs.html')

def developers(request):
    devs = User.objects.order_by('username')
    return render_response(request, 'public/developers.html', {'devs':devs})

def donate(request):
    donor_count = Donator.objects.count()
    splitval = donor_count / 4
    slice1 = Donator.objects.all()[:splitval]
    slice2 = Donator.objects.all()[(splitval):(splitval*2)]
    slice3 = Donator.objects.all()[(splitval*2):(donor_count-splitval)]
    slice4 = Donator.objects.all()[(donor_count-splitval):donor_count]
    return render_response(request, 'public/donate.html',
        {'slice1':slice1,'slice2':slice2,'slice3':slice3,'slice4':slice4})

def download(request):
    mirrors = Mirror.objects.order_by('country', 'domain')
    return render_response(request, 'public/download.html', {'mirrors':mirrors})

def irc(request):
    return render_response(request, 'public/irc.html')

def moreforums(request):
    return render_response(request, 'public/moreforums.html')

def press(request):
    return render_response(request, 'public/press.html')

def projects(request):
    return render_response(request, 'public/projects.html')

def robots(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", mimetype="text/plain")

def denied(request):
    return render_response(request, 'public/denied.html')

# vim: set ts=4 sw=4 et:


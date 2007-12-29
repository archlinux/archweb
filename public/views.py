from django.http import HttpResponse
from archweb_dev.utils import render_template
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
	return render_template('public/index.html', request, {'news_updates':news,'pkg_updates':pkgs,'repos':repos})

def about(request):
	return render_template('public/about.html', request)

def art(request):
	return render_template('public/art.html', request)

def cvs(request):
	return render_template('public/cvs.html', request)

def developers(request):
	devs = User.objects.order_by('username')
	return render_template('public/developers.html', request, {'devs':devs})

def donate(request):
	donor_count = Donator.objects.count()
	splitval = donor_count / 4
	slice1 = Donator.objects.all()[:splitval]
	slice2 = Donator.objects.all()[(splitval):(splitval*2)]
	slice3 = Donator.objects.all()[(splitval*2):(donor_count-splitval)]
	slice4 = Donator.objects.all()[(donor_count-splitval):donor_count]
	return render_template('public/donate.html', request,
		{'slice1':slice1,'slice2':slice2,'slice3':slice3,'slice4':slice4})

def download(request):
	mirrors = Mirror.objects.order_by('country', 'domain')
	return render_template('public/download.html', request, {'mirrors':mirrors})

def irc(request):
	return render_template('public/irc.html', request)

def moreforums(request):
	return render_template('public/moreforums.html', request)

def press(request):
	return render_template('public/press.html', request)

def projects(request):
	return render_template('public/projects.html', request)

def robots(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", mimetype="text/plain")

def denied(request):
	return render_template('public/denied.html', request)

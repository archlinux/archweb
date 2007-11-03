from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import validators
from archlinux.utils import render_template
from archlinux.packages.models import Package
from archlinux.todolists.models import Todolist, TodolistPkg
from archlinux.settings import DATA_DIR
from archlinux.utils import validate
from archlinux.common.models import UserProfile

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

	return render_template('devel/index.html', request,
		{'stats':stats, 'pkgs':pkgs, 'todos':todos, 'maint':thismaint})

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
	return render_template('devel/profile.html', request, {'errors':errors,'email':request.user.email})

@login_required
def guide(request):
	return HttpResponse(file(DATA_DIR + '/pkgmaint_guide.txt').read(),
			mimetype='text/plain')

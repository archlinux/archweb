from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django import forms
from archlinux.utils import render_template
from archlinux.news.models import News
from datetime import date

def view(request, newsid):
	news = get_object_or_404(News, id=newsid)
	return render_template('news/view.html', request, {'news':news})

def list(request):
	news = News.objects.order_by('-postdate', '-id')
	return render_template('news/list.html', request, {'news':news})

@user_passes_test(lambda u: u.has_perm('news.add_news'))
def add(request):
	try:
		m = User.objects.get(username=request.user.username)
	except User.DoesNotExist:
		return render_template('error_page.html', request,
			{'errmsg': 'Cannot find a maintainer record for you!  No posting allowed.'})

	manipulator = News.AddManipulator()
	if request.POST:
		data = request.POST.copy()
		# add in the author ID
		data['author'] = m.id
		errors = manipulator.get_validation_errors(data)
		if not errors:
			manipulator.do_html2python(data)
			manipulator.save(data)
			return HttpResponseRedirect('/news/')
	else:
		errors = {}
		data   = {}

	form = forms.FormWrapper(manipulator, data, errors)
	return render_template('news/add.html', request, {'form': form})

@user_passes_test(lambda u: u.has_perm('news.delete_news'))
def delete(request, newsid):
	news = get_object_or_404(News, id=newsid)
	#if news.author.id != request.user.id:
	#	return render_template('error_page.html', request, {'errmsg': 'You do not own this news item'})
	if request.POST:
		news.delete()
		return HttpResponseRedirect('/news/')
	return render_template('news/delete.html', request)

@user_passes_test(lambda u: u.has_perm('news.change_news'))
def edit(request, newsid):
	try:
		m = User.objects.get(username=request.user.username)
	except User.DoesNotExist:
		return render_template('error_page.html', request,
			{'errmsg': 'Cannot find a maintainer record for you!  No posting allowed.'})
	try:
		manipulator = News.ChangeManipulator(newsid)
	except News.DoesNotExist:
		raise Http404

	news = manipulator.original_object
#	if news.author != m:
#		return render_template('error_page.html', request, {'errmsg': 'You do not own this news item'})
	if request.POST:
		data = request.POST.copy()
		# add in the author ID
		data['author'] = news.author.id
		errors = manipulator.get_validation_errors(data)
		if not errors:
			manipulator.do_html2python(data)
			manipulator.save(data)
			return HttpResponseRedirect('/news/')
	else:
		errors = {}
		data   = news.__dict__

	form = forms.FormWrapper(manipulator, data, errors)
	return render_template('news/add.html', request, {'form': form, 'news':news})

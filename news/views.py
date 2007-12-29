from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django import forms
from archweb_dev.lib.utils import render_response
from archweb_dev.news.models import News
from datetime import date

def view(request, newsid):
    news = get_object_or_404(News, id=newsid)
    return render_response(request, 'news/view.html', {'news':news})

def list(request):
    news = News.objects.order_by('-postdate', '-id')
    return render_response(request, 'news/list.html', {'news':news})

@user_passes_test(lambda u: u.has_perm('news.add_news'))
def add(request):
    try:
        m = User.objects.get(username=request.user.username)
    except User.DoesNotExist:
        return render_response(request, 'error_page.html',
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
    return render_response(request, 'news/add.html', {'form': form})

@user_passes_test(lambda u: u.has_perm('news.delete_news'))
def delete(request, newsid):
    news = get_object_or_404(News, id=newsid)
    #if news.author.id != request.user.id:
    #   return render_response(request, 'error_page.html', {'errmsg': 'You do not own this news item'})
    if request.POST:
        news.delete()
        return HttpResponseRedirect('/news/')
    return render_response(request, 'news/delete.html')

@user_passes_test(lambda u: u.has_perm('news.change_news'))
def edit(request, newsid):
    try:
        m = User.objects.get(username=request.user.username)
    except User.DoesNotExist:
        return render_response(request, 'error_page.html',
            {'errmsg': 'Cannot find a maintainer record for you!  No posting allowed.'})
    try:
        manipulator = News.ChangeManipulator(newsid)
    except News.DoesNotExist:
        raise Http404

    news = manipulator.original_object
#   if news.author != m:
#       return render_response(request, 'error_page.html', {'errmsg': 'You do not own this news item'})
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
    return render_response(request, 'news/add.html', {'form': form, 'news':news})

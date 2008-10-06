from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import News

from django.views.generic import list_detail, create_update

def view(request, newsid):
    return list_detail.object_detail(request, News.objects.all(), newsid,
            template_name="news/view.html",
            template_object_name='news')

#TODO: May as well use a date-based list here sometime
def list(request):
    return list_detail.object_list(request, News.objects.all(),
            template_name="news/list.html",
            template_object_name="news")

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        exclude=('id', 'author', 'postdate')

@permission_required('main.add_news')
def add(request):
    return create_update.create_object(request,
            form_class=NewsForm,
            template_name='news/add.html')

@permission_required('main.delete_news')
def delete(request, newsid):
    return create_update.delete_object(request,
            News,
            object_id=newsid,
            post_delete_redirect='/news/',
            template_name='news/delete.html',
            template_object_name='news')

@permission_required('main.change_news')
def edit(request, newsid):
    return create_update.update_object(request, object_id=newsid,
            form_class=NewsForm,
            template_name="news/add.html")

# vim: set ts=4 sw=4 et:


from django import forms
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.views.generic import list_detail, create_update

from main.models import News

def view(request, newsid):
    return list_detail.object_detail(request, News.objects.all(), newsid,
            template_name="news/view.html",
            template_object_name='news')

#TODO: May as well use a date-based list here sometime
def list(request):
    return list_detail.object_list(request,
            News.objects.all().select_related('author').defer('content'),
            template_name="news/list.html",
            template_object_name="news")

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        exclude=('id', 'author', 'postdate')

@permission_required('main.add_news')
@never_cache
def add(request):
    if request.POST:
        form = NewsForm(request.POST)
        if form.is_valid():
            newsitem = form.save(commit=False)
            newsitem.author = request.user
            newsitem.save()
            return redirect(newsitem.get_absolute_url())
    else:
        form = NewsForm()
    return render_to_response('news/add.html',
            RequestContext(request, { 'form': form }))

@permission_required('main.delete_news')
@never_cache
def delete(request, newsid):
    return create_update.delete_object(request,
            News,
            object_id=newsid,
            post_delete_redirect='/news/',
            template_name='news/delete.html',
            template_object_name='news')

@permission_required('main.change_news')
@never_cache
def edit(request, newsid):
    return create_update.update_object(request,
            object_id=newsid,
            form_class=NewsForm,
            template_name="news/add.html")

# vim: set ts=4 sw=4 et:

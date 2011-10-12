from django import forms
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.views.decorators.cache import never_cache
from django.views.generic import list_detail, create_update
from django.views.generic.simple import direct_to_template

import markdown

from .models import News

def view_redirect(request, object_id):
    newsitem = get_object_or_404(News, pk=object_id)
    return redirect(newsitem, permanent=True)

def view(request, slug=None):
    return list_detail.object_detail(request, News.objects.all(),
            slug=slug,
            template_name="news/view.html",
            template_object_name='news')

#TODO: May as well use a date-based list here sometime
def news_list(request):
    return list_detail.object_list(request,
            News.objects.all().select_related('author').defer('content'),
            paginate_by=50,
            template_name="news/list.html",
            template_object_name="news")

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        exclude = ('id', 'slug', 'author', 'postdate')

def find_unique_slug(newsitem):
    '''Attempt to find a unique slug for this news item.'''
    existing = list(News.objects.values_list('slug', flat=True).distinct())

    suffixed = slug = slugify(newsitem.title)
    suffix = 0
    while suffixed in existing:
        suffix += 1
        suffixed = "%s-%d" % (slug, suffix)

    return suffixed

@permission_required('news.add_news')
@never_cache
def add(request):
    if request.POST:
        form = NewsForm(request.POST)
        if form.is_valid():
            newsitem = form.save(commit=False)
            newsitem.author = request.user
            newsitem.slug = find_unique_slug(newsitem)
            newsitem.save()
            return redirect(newsitem)
    else:
        form = NewsForm()
    return direct_to_template(request, 'news/add.html', { 'form': form })

@permission_required('news.delete_news')
@never_cache
def delete(request, slug):
    return create_update.delete_object(request,
            News,
            slug=slug,
            post_delete_redirect='/news/',
            template_name='news/delete.html',
            template_object_name='news')

@permission_required('news.change_news')
@never_cache
def edit(request, slug):
    return create_update.update_object(request,
            slug=slug,
            form_class=NewsForm,
            template_name="news/add.html")

@permission_required('news.change_news')
@never_cache
def preview(request):
    markup = ''
    if request.POST:
        data = request.POST.get('data', '')
        markup = markdown.markdown(data)
    return HttpResponse(markup)

# vim: set ts=4 sw=4 et:

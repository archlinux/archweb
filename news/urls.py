from django.conf.urls import patterns
from django.contrib.auth.decorators import permission_required
from .views import (NewsDetailView, NewsListView,
        NewsCreateView, NewsEditView, NewsDeleteView)


urlpatterns = patterns('news.views',
    (r'^$',
        NewsListView.as_view(), {}, 'news-list'),

    (r'^preview/$', 'preview'),
    # old news URLs, permanent redirect view so we don't break all links
    (r'^(?P<object_id>\d+)/$', 'view_redirect'),

    (r'^add/$',
        permission_required('news.add_news')(NewsCreateView.as_view())),
    (r'^(?P<slug>[-\w]+)/$',
        NewsDetailView.as_view()),
    (r'^(?P<slug>[-\w]+)/edit/$',
        permission_required('news.change_news')(NewsEditView.as_view())),
    (r'^(?P<slug>[-\w]+)/delete/$',
        permission_required('news.delete_news')(NewsDeleteView.as_view())),
)

# vim: set ts=4 sw=4 et:

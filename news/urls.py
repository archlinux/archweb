from django.conf.urls import url
from django.contrib.auth.decorators import permission_required
from .views import (NewsDetailView, NewsListView,
        NewsCreateView, NewsEditView, NewsDeleteView)

import views


urlpatterns = [
    url(r'^$', NewsListView.as_view(), name='news-list'),

    url(r'^preview/$', views.preview),
    # old news URLs, permanent redirect view so we don't break all links
    url(r'^(?P<object_id>\d+)/$', views.view_redirect),

    url(r'^add/$',
        permission_required('news.add_news')(NewsCreateView.as_view())),
    url(r'^(?P<slug>[-\w]+)/$',
        NewsDetailView.as_view()),
    url(r'^(?P<slug>[-\w]+)/edit/$',
        permission_required('news.change_news')(NewsEditView.as_view())),
    url(r'^(?P<slug>[-\w]+)/delete/$',
        permission_required('news.delete_news')(NewsDeleteView.as_view())),
]

# vim: set ts=4 sw=4 et:

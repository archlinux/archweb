from django.urls import re_path
from django.contrib.auth.decorators import permission_required
from .views import (NewsDetailView, NewsListView, NewsCreateView, NewsEditView,
                    NewsDeleteView, preview, view_redirect)


urlpatterns = [
    re_path(r'^$', NewsListView.as_view(), name='news-list'),

    re_path(r'^preview/$', preview),
    # old news URLs, permanent redirect view so we don't break all links
    re_path(r'^(?P<object_id>\d+)/$', view_redirect),

    re_path(r'^add/$',
            permission_required('news.add_news')(NewsCreateView.as_view())),
    re_path(r'^(?P<slug>[-\w]+)/$',
            NewsDetailView.as_view()),
    re_path(r'^(?P<slug>[-\w]+)/edit/$',
            permission_required('news.change_news')(NewsEditView.as_view())),
    re_path(r'^(?P<slug>[-\w]+)/delete/$',
            permission_required('news.delete_news')(NewsDeleteView.as_view())),
]

# vim: set ts=4 sw=4 et:

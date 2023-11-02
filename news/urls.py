from django.contrib.auth.decorators import permission_required
from django.urls import path, re_path

from .views import (
    NewsCreateView,
    NewsDeleteView,
    NewsDetailView,
    NewsEditView,
    NewsListView,
    preview,
    view_redirect,
)

urlpatterns = [
    path('', NewsListView.as_view(), name='news-list'),

    path('preview/', preview),
    # old news URLs, permanent redirect view so we don't break all links
    re_path(r'^(?P<object_id>\d+)/$', view_redirect),

    path('add/',
         permission_required('news.add_news')(NewsCreateView.as_view())),
    re_path(r'^(?P<slug>[-\w]+)/$',
            NewsDetailView.as_view()),
    re_path(r'^(?P<slug>[-\w]+)/edit/$',
            permission_required('news.change_news')(NewsEditView.as_view())),
    re_path(r'^(?P<slug>[-\w]+)/delete/$',
            permission_required('news.delete_news')(NewsDeleteView.as_view())),
]

# vim: set ts=4 sw=4 et:

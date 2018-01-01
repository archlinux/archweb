from django.conf.urls import url
from django.contrib.auth.decorators import permission_required

from .views import (view_redirect, view, add, edit, flag,
        list_pkgbases, DeleteTodolist, TodolistListView)

urlpatterns = [
    url(r'^$', TodolistListView.as_view(), name='todolist-list'),

    # old todolists URLs, permanent redirect view so we don't break all links
    url(r'^(?P<old_id>\d+)/$', view_redirect),

    url(r'^add/$',
        permission_required('todolists.add_todolist')(add)),
    url(r'^(?P<slug>[-\w]+)/$', view),
    url(r'^(?P<slug>[-\w]+)/edit/$',
        permission_required('todolists.change_todolist')(edit)),
    url(r'^(?P<slug>[-\w]+)/delete/$',
        permission_required('todolists.delete_todolist')(DeleteTodolist.as_view())),
    url(r'^(?P<slug>[-\w]+)/flag/(?P<pkg_id>\d+)/$',
        permission_required('todolists.change_todolistpackage')(flag)),
    url(r'^(?P<slug>[-\w]+)/pkgbases/(?P<svn_root>[a-z]+)/$',
        list_pkgbases),
]

# vim: set ts=4 sw=4 et:

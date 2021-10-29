from django.urls import re_path
from django.contrib.auth.decorators import permission_required

from .views import (view, view_json, add, edit, flag,
                    list_pkgbases, DeleteTodolist, TodolistListView)

urlpatterns = [
    re_path(r'^$', TodolistListView.as_view(), name='todolist-list'),

    re_path(r'^add/$',
        permission_required('todolists.add_todolist')(add)),
    re_path(r'^(?P<slug>[-\w]+)/$', view),
    re_path(r'^(?P<slug>[-\w]+)/json$', view_json),
    re_path(r'^(?P<slug>[-\w]+)/edit/$',
        permission_required('todolists.change_todolist')(edit)),
    re_path(r'^(?P<slug>[-\w]+)/delete/$',
        permission_required('todolists.delete_todolist')(DeleteTodolist.as_view())),
    re_path(r'^(?P<slug>[-\w]+)/flag/(?P<pkg_id>\d+)/$',
        permission_required('todolists.change_todolistpackage')(flag)),
    re_path(r'^(?P<slug>[-\w]+)/pkgbases/(?P<svn_root>[a-z]+)/$',
        list_pkgbases),
]

# vim: set ts=4 sw=4 et:

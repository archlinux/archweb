from django.contrib.auth.decorators import permission_required
from django.urls import path, re_path

from .views import (
    DeleteTodolist,
    TodolistListView,
    add,
    edit,
    flag,
    list_pkgbases,
    view,
    view_json,
)

urlpatterns = [
    path('', TodolistListView.as_view(), name='todolist-list'),

    path('add/',
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

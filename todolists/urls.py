from django.conf.urls import patterns
from django.contrib.auth.decorators import permission_required

from .views import (view_redirect, view, todolist_list, add, edit, flag,
        list_pkgbases, DeleteTodolist)

urlpatterns = patterns('',
    (r'^$', todolist_list),

    # old todolists URLs, permanent redirect view so we don't break all links
    (r'^(?P<old_id>\d+)/$', view_redirect),

    (r'^add/$',
        permission_required('todolists.add_todolist')(add)),
    (r'^(?P<slug>[-\w]+)/$', view),
    (r'^(?P<slug>[-\w]+)/edit/$',
        permission_required('todolists.change_todolist')(edit)),
    (r'^(?P<slug>[-\w]+)/delete/$',
        permission_required('todolists.delete_todolist')(DeleteTodolist.as_view())),
    (r'^(?P<slug>[-\w]+)/flag/(?P<pkg_id>\d+)/$',
        permission_required('todolists.change_todolistpackage')(flag)),
    (r'^(?P<slug>[-\w]+)/pkgbases/(?P<svn_root>[a-z]+)/$',
        list_pkgbases),
)

# vim: set ts=4 sw=4 et:

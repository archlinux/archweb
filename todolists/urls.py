from django.conf.urls import patterns
from django.contrib.auth.decorators import permission_required

from .views import DeleteTodolist

urlpatterns = patterns('todolists.views',
    (r'^$',                       'todolist_list'),
    (r'^(?P<list_id>\d+)/$',      'view'),
    (r'^(?P<list_id>\d+)/pkgbases/(?P<svn_root>[a-z]+)/$', 'list_pkgbases'),
    (r'^add/$',                   'add'),
    (r'^edit/(?P<list_id>\d+)/$', 'edit'),
    (r'^flag/(\d+)/(\d+)/$',      'flag'),
    (r'^delete/(?P<pk>\d+)/$',
        permission_required('main.delete_todolist')(DeleteTodolist.as_view())),
)

# vim: set ts=4 sw=4 et:

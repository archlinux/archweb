from django.conf.urls.defaults import patterns

urlpatterns = patterns('todolists.views',
    (r'^$',                       'list'),
    (r'^(\d+)/$',                 'view'),
    (r'^add/$',                   'add'),
    (r'^edit/(?P<list_id>\d+)/$', 'edit'),
    (r'^flag/(\d+)/(\d+)/$',      'flag'),
    (r'^delete/(?P<object_id>\d+)/$',
        'delete_todolist'),
)

# vim: set ts=4 sw=4 et:

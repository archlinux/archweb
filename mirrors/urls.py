from django.conf.urls import patterns

urlpatterns = patterns('mirrors.views',
    (r'^$',                     'mirrors', {}, 'mirror-list'),
    (r'^status/$',              'status',  {}, 'mirror-status'),
    (r'^status/json/$',         'status_json',  {}, 'mirror-status-json'),
    (r'^(?P<name>[\.\-\w]+)/$', 'mirror_details'),
)

# vim: set ts=4 sw=4 et:

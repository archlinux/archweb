from django.conf.urls import patterns

urlpatterns = patterns('mirrors.views',
    (r'^$',                     'mirrors', {}, 'mirror-list'),
    (r'^status/$',              'status',  {}, 'mirror-status'),
    (r'^status/json/$',         'status_json',  {}, 'mirror-status-json'),
    (r'^status/tier/(?P<tier>\d+)/$', 'status', {}, 'mirror-status-tier'),
    (r'^status/tier/(?P<tier>\d+)/json/$', 'status_json', {}, 'mirror-status-tier-json'),
    (r'^locations/json/$',      'locations_json',  {}, 'mirror-locations-json'),
    (r'^(?P<name>[\.\-\w]+)/$', 'mirror_details'),
    (r'^(?P<name>[\.\-\w]+)/json/$', 'mirror_details_json'),
)

# vim: set ts=4 sw=4 et:

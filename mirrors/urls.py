from django.conf.urls import patterns

from .views import mirrors, status, mirror_details, url_details
from .views.api import status_json, mirror_details_json, locations_json

urlpatterns = patterns('',
    (r'^$', mirrors, {}, 'mirror-list'),
    (r'^status/$', status,  {}, 'mirror-status'),
    (r'^status/json/$', status_json,  {}, 'mirror-status-json'),
    (r'^status/tier/(?P<tier>\d+)/$', status, {}, 'mirror-status-tier'),
    (r'^status/tier/(?P<tier>\d+)/json/$', status_json, {}, 'mirror-status-tier-json'),
    (r'^locations/json/$', locations_json,  {}, 'mirror-locations-json'),
    (r'^(?P<name>[\.\-\w]+)/$', mirror_details),
    (r'^(?P<name>[\.\-\w]+)/json/$', mirror_details_json),
    (r'^(?P<name>[\.\-\w]+)/(?P<url_id>\d+)/$', url_details),
)

# vim: set ts=4 sw=4 et:

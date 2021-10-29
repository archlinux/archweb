from django.urls import re_path
from django.views.decorators.cache import cache_page

from .views import mirrors, status, mirror_details, url_details
from .views.api import status_json, mirror_details_json, locations_json

urlpatterns = [
    re_path(r'^$', mirrors, name='mirror-list'),
    re_path(r'^tier/(?P<tier>\d+)/$', mirrors, name='mirror-list-tier'),
    re_path(r'^status/$', status, name='mirror-status'),
    re_path(r'^status/json/$', status_json, name='mirror-status-json'),
    re_path(r'^status/tier/(?P<tier>\d+)/$', status, name='mirror-status-tier'),
    re_path(r'^status/tier/(?P<tier>\d+)/json/$', status_json, name='mirror-status-tier-json'),
    re_path(r'^locations/json/$', cache_page(317)(locations_json), name='mirror-locations-json'),
    re_path(r'^(?P<name>[\.\-\w]+)/$', mirror_details),
    re_path(r'^(?P<name>[\.\-\w]+)/json/$', mirror_details_json),
    re_path(r'^(?P<name>[\.\-\w]+)/(?P<url_id>\d+)/$', url_details),
]

# vim: set ts=4 sw=4 et:

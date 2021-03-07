from django.conf.urls import url
from django.views.decorators.cache import cache_page

from .views import mirrors, status, mirror_details, url_details
from .views.api import status_json, mirror_details_json, locations_json

urlpatterns = [
    url(r'^$', mirrors, name='mirror-list'),
    url(r'^tier/(?P<tier>\d+)/$', mirrors, name='mirror-list-tier'),
    url(r'^status/$', status, name='mirror-status'),
    url(r'^status/json/$', cache_page(317)(status_json), name='mirror-status-json'),
    url(r'^status/tier/(?P<tier>\d+)/$', status, name='mirror-status-tier'),
    url(r'^status/tier/(?P<tier>\d+)/json/$', status_json, name='mirror-status-tier-json'),
    url(r'^locations/json/$', cache_page(317)(locations_json), name='mirror-locations-json'),
    url(r'^(?P<name>[\.\-\w]+)/$', mirror_details),
    url(r'^(?P<name>[\.\-\w]+)/json/$', cache_page(317)(mirror_details_json)),
    url(r'^(?P<name>[\.\-\w]+)/(?P<url_id>\d+)/$', url_details),
]

# vim: set ts=4 sw=4 et:

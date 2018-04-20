from django.conf.urls import url

from packages.views import groups, group_details

urlpatterns = [
    url(r'^$', groups, name='groups-list'),
    url(r'^(?P<arch>[A-z0-9]+)/$', groups),
    url(r'^(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/$', group_details),
]

# vim: set ts=4 sw=4 et:

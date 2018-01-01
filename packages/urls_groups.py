from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.groups, name='groups-list'),
    url(r'^(?P<arch>[A-z0-9]+)/$', views.groups),
    url(r'^(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/$', views.group_details),
]

# vim: set ts=4 sw=4 et:

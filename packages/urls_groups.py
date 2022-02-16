from django.urls import re_path, path
from packages.views import search
from packages.views.display import groups, group_details

urlpatterns = [
    path('', groups, name='groups-list'),
    path('search/json/', search.group_search_json),
    re_path(r'^(?P<arch>[A-z0-9]+)/$', groups),
    re_path(r'^(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/$', group_details),
]

# vim: set ts=4 sw=4 et:

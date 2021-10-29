from django.conf.urls import include
from django.urls import re_path
from .views import ReleaseListView, ReleaseDetailView
from releng import views

releases_patterns = [
    re_path(r'^$', ReleaseListView.as_view(), name='releng-release-list'),
    re_path(r'^json/$', views.releases_json, name='releng-release-list-json'),
    re_path(r'^(?P<version>[-.\w]+)/$', ReleaseDetailView.as_view(), name='releng-release-detail'),
    re_path(r'^(?P<version>[-.\w]+)/torrent/$', views.release_torrent, name='releng-release-torrent'),
]

netboot_patterns = [
    re_path(r'^archlinux\.ipxe$', views.netboot_config, name='releng-netboot-config'),
    re_path(r'^$', views.netboot_info, name='releng-netboot-info')
]

urlpatterns = [
    re_path(r'^releases/', include(releases_patterns)),
    re_path(r'^netboot/', include(netboot_patterns)),
]

# vim: set ts=4 sw=4 et:

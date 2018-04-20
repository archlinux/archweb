from django.conf.urls import include, url

from .views import ReleaseListView, ReleaseDetailView
from releng import views

releases_patterns = [
    url(r'^$', ReleaseListView.as_view(), name='releng-release-list'),
    url(r'^json/$', views.releases_json, name='releng-release-list-json'),
    url(r'^(?P<version>[-.\w]+)/$', ReleaseDetailView.as_view(), name='releng-release-detail'),
    url(r'^(?P<version>[-.\w]+)/torrent/$', views.release_torrent, name='releng-release-torrent'),
]

netboot_patterns = [
    url(r'^archlinux\.ipxe$', views.netboot_config, name='releng-netboot-config'),
    url(r'^$', views.netboot_info, name='releng-netboot-info')
]

urlpatterns = [
    url(r'^releases/', include(releases_patterns)),
    url(r'^netboot/', include(netboot_patterns)),
]

# vim: set ts=4 sw=4 et:

from django.conf.urls import include
from django.urls import path, re_path

from releng import views

from .views import ReleaseDetailView, ReleaseListView

releases_patterns = [
    path('', ReleaseListView.as_view(), name='releng-release-list'),
    path('json/', views.releases_json, name='releng-release-list-json'),
    re_path(r'^(?P<version>[-.\w]+)/$', ReleaseDetailView.as_view(), name='releng-release-detail'),
    re_path(r'^(?P<version>[-.\w]+)/torrent/$', views.release_torrent, name='releng-release-torrent'),
]

netboot_patterns = [
    path('archlinux.ipxe', views.netboot_config, name='releng-netboot-config'),
    path('', views.netboot_info, name='releng-netboot-info')
]

urlpatterns = [
    path('releases/', include(releases_patterns)),
    path('netboot/', include(netboot_patterns)),
]

# vim: set ts=4 sw=4 et:

from django.conf.urls import include, patterns

from .views import ReleaseListView, ReleaseDetailView

releases_patterns = patterns('releng.views',
    (r'^$',
        ReleaseListView.as_view(), {}, 'releng-release-list'),
    (r'^json/$',
        'releases_json', {}, 'releng-release-list-json'),
    (r'^(?P<version>[-.\w]+)/$',
        ReleaseDetailView.as_view(), {}, 'releng-release-detail'),
    (r'^(?P<version>[-.\w]+)/torrent/$',
        'release_torrent', {}, 'releng-release-torrent'),
)

netboot_patterns = patterns('releng.views',
    (r'^archlinux\.ipxe$', 'netboot_config', {}, 'releng-netboot-config'),
    (r'^$', 'netboot_info', {}, 'releng-netboot-info')
)

urlpatterns = patterns('',
    (r'^releases/', include(releases_patterns)),
    (r'^netboot/', include(netboot_patterns)),
)

# vim: set ts=4 sw=4 et:

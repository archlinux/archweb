from django.conf.urls import include, patterns

from .views import ReleaseListView, ReleaseDetailView

feedback_patterns = patterns('releng.views',
    (r'^$',                              'test_results_overview', {}, 'releng-test-overview'),
    (r'^submit/$',                       'submit_test_result', {}, 'releng-test-submit'),
    (r'^thanks/$',                       'submit_test_thanks', {}, 'releng-test-thanks'),
    (r'^iso/(?P<iso_id>\d+)/$',          'test_results_iso', {}, 'releng-results-iso'),
    (r'^(?P<option>.+)/(?P<value>\d+)/$','test_results_for', {}, 'releng-results-for'),
    (r'^iso/overview/$',                 'iso_overview', {}, 'releng-iso-overview'),
)

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
    (r'^archlinux\.ipxe$', 'netboot_config', {}, 'releng-netboot-config')
)

urlpatterns = patterns('',
    (r'^feedback/', include(feedback_patterns)),
    (r'^releases/', include(releases_patterns)),
    (r'^netboot/', include(netboot_patterns)),
)

# vim: set ts=4 sw=4 et:

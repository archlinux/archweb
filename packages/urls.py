from django.conf.urls import include, patterns

from .views.search import SearchListView

package_patterns = patterns('packages.views',
    (r'^$',            'details'),
    (r'^json/$',       'details_json'),
    (r'^files/$',      'files'),
    (r'^files/json/$', 'files_json'),
    (r'^flag/$',       'flag'),
    (r'^flag/done/$',  'flag_confirmed', {}, 'package-flag-confirmed'),
    (r'^unflag/$',     'unflag'),
    (r'^unflag/all/$', 'unflag_all'),
    (r'^signoff/$',    'signoff_package'),
    (r'^signoff/revoke/$', 'signoff_package', {'revoke': True}),
    (r'^signoff/options/$', 'signoff_options'),
    (r'^download/$',   'download'),
)

urlpatterns = patterns('packages.views',
    (r'^flaghelp/$', 'flaghelp'),
    (r'^signoffs/$', 'signoffs', {}, 'package-signoffs'),
    (r'^signoffs/json/$', 'signoffs_json', {}, 'package-signoffs-json'),
    (r'^update/$',   'update'),

    (r'^$', SearchListView.as_view(), {}, 'packages-search'),
    (r'^search/json/$', 'search_json'),

    (r'^differences/$',          'arch_differences', {}, 'packages-differences'),
    (r'^stale_relations/$',      'stale_relations'),
    (r'^stale_relations/update/$','stale_relations_update'),

    (r'^(?P<name>[^ /]+)/$',
        'details'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[^ /]+)/$',
        'details'),
    # canonical package url. subviews defined above
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/',
        include(package_patterns)),
)

# vim: set ts=4 sw=4 et:

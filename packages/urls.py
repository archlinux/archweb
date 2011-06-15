from django.conf.urls.defaults import include, patterns

package_patterns = patterns('packages.views',
    (r'^$',            'details'),
    (r'^json/$',       'details_json'),
    (r'^files/$',      'files'),
    (r'^files/json/$', 'files_json'),
    (r'^flag/$',       'flag'),
    (r'^flag/done/$',  'flag_confirmed', {}, 'package-flag-confirmed'),
    (r'^unflag/$',     'unflag'),
    (r'^unflag/all/$', 'unflag_all'),
    (r'^download/$',   'download'),
)

urlpatterns = patterns('packages.views',
    (r'^flaghelp/$', 'flaghelp'),
    (r'^signoffs/$', 'signoffs', {}, 'package-signoffs'),
    (r'^signoff_package/(?P<arch>[A-z0-9]+)/(?P<pkgname>[A-z0-9\-+.]+)/$',
        'signoff_package'),
    (r'^update/$',   'update'),

    (r'^$',                      'search', {}, 'packages-search'),
    (r'^(?P<page>\d+)/$',        'search'),

    (r'^differences/$',          'arch_differences', {}, 'packages-differences'),
    (r'^stale_relations/$',      'stale_relations'),
    (r'^stale_relations/update/$','stale_relations_update'),

    (r'^(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    # canonical package url. subviews defined above
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/',
        include(package_patterns)),
)

# vim: set ts=4 sw=4 et:

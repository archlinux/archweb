from django.conf.urls.defaults import patterns

urlpatterns = patterns('packages.views',
    (r'^flaghelp/$', 'flaghelp'),
    (r'^signoffs/$', 'signoffs'),
    (r'^signoff_package/(?P<arch>[A-z0-9]+)/(?P<pkgname>[A-z0-9\-+.]+)/$',
        'signoff_package'),
    (r'^update/$',   'update'),

    # Preference is for the non-search url below, but search is kept
    # because other projects link to it
    (r'^search/$',               'search'),
    (r'^search/(?P<page>\d+)/$', 'search'),
    (r'^$',                      'search'),
    (r'^(?P<page>\d+)/$',        'search'),

    (r'^differences/$',          'arch_differences'),

    (r'^(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/files/$',
        'files'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/maintainer/$',
        'getmaintainer'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/flag/$',
        'flag'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/unflag/$',
        'unflag'),
    (r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/download/$',
        'download'),
)

# vim: set ts=4 sw=4 et:

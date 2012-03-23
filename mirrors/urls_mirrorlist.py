from django.conf.urls import patterns

urlpatterns = patterns('mirrors.views',
    (r'^$',         'generate_mirrorlist', {}, 'mirrorlist'),
    (r'^all/$',     'find_mirrors', {'countries': ['all']}),
    (r'^all/ftp/$', 'find_mirrors',
        {'countries': ['all'], 'protocols': ['ftp']}),
    (r'^all/http/$', 'find_mirrors',
        {'countries': ['all'], 'protocols': ['http']}),
)

# vim: set ts=4 sw=4 et:

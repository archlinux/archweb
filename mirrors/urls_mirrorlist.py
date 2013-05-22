from django.conf.urls import patterns


urlpatterns = patterns('mirrors.views',
    (r'^$',         'generate_mirrorlist', {}, 'mirrorlist'),
    (r'^all/$',     'find_mirrors', {'countries': ['all']}),
    (r'^all/(?P<protocol>[A-z]+)/$', 'find_mirrors_simple',
        {}, 'mirrorlist_simple')
)

# vim: set ts=4 sw=4 et:

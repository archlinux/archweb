from django.conf.urls.defaults import patterns

urlpatterns = patterns('devel.views',
    (r'^admin_log/$','admin_log'),
    (r'^admin_log/(?P<username>.*)/$','admin_log'),
    (r'^clock/$',    'clock'),
    (r'^$',          'index'),
    (r'^newuser/$',  'new_user_form'),
    (r'^profile/$',  'change_profile'),
    (r'^reports/(?P<report>.*)/(?P<username>.*)/$', 'report'),
    (r'^reports/(?P<report>.*)/$', 'report'),
)

# vim: set ts=4 sw=4 et:

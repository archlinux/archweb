from django.conf.urls import patterns

urlpatterns = patterns('devel.views',
    (r'^admin_log/$','admin_log'),
    (r'^admin_log/(?P<username>.*)/$','admin_log'),
    (r'^clock/$',    'clock', {},     'devel-clocks'),
    (r'^$',          'index', {},     'devel-index'),
    (r'^stats/$',    'stats', {},     'devel-stats'),
    (r'^newuser/$',  'new_user_form'),
    (r'^profile/$',  'change_profile'),
    (r'^reports/(?P<report_name>.*)/(?P<username>.*)/$', 'report'),
    (r'^reports/(?P<report_name>.*)/$', 'report'),
)

# vim: set ts=4 sw=4 et:

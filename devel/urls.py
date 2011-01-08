from django.conf.urls.defaults import patterns

urlpatterns = patterns('devel.views',
    (r'^$',          'index'),
    (r'^clock/$',    'clock'),
    (r'^notify/$',   'change_notify'),
    (r'^profile/$',  'change_profile'),
    (r'^newuser/$',  'new_user_form'),
)

# vim: set ts=4 sw=4 et:

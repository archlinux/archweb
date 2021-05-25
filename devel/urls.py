from django.conf.urls import url

from devel import views


urlpatterns = [
    url(r'^admin_log/$', views.admin_log),
    url(r'^admin_log/(?P<username>.*)/$', views.admin_log),
    url(r'^clock/$',    views.clock, name='devel-clocks'),
    url(r'^tier0mirror/$',    views.tier0_mirror, name='tier0-mirror'),
    url(r'^mirrorauth/$',    views.tier0_mirror_auth, name='tier0-mirror-atuh'),
    url(r'^$',          views.index, name='devel-index'),
    url(r'^stats/$',    views.stats, name='devel-stats'),
    url(r'^newuser/$',  views.new_user_form),
    url(r'^profile/$',  views.change_profile),
    url(r'^reports/(?P<report_name>.*)/(?P<username>.*)/$', views.report),
    url(r'^reports/(?P<report_name>.*)/$', views.report),
]

# vim: set ts=4 sw=4 et:

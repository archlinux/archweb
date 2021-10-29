from django.urls import re_path

from devel import views


urlpatterns = [
    re_path(r'^admin_log/$', views.admin_log),
    re_path(r'^admin_log/(?P<username>.*)/$', views.admin_log),
    re_path(r'^clock/$',    views.clock, name='devel-clocks'),
    re_path(r'^tier0mirror/$',    views.tier0_mirror, name='tier0-mirror'),
    re_path(r'^mirrorauth/$',    views.tier0_mirror_auth, name='tier0-mirror-atuh'),
    re_path(r'^$',          views.index, name='devel-index'),
    re_path(r'^stats/$',    views.stats, name='devel-stats'),
    re_path(r'^newuser/$',  views.new_user_form),
    re_path(r'^profile/$',  views.change_profile),
    re_path(r'^reports/(?P<report_name>.*)/(?P<username>.*)/$', views.report),
    re_path(r'^reports/(?P<report_name>.*)/$', views.report),
]

# vim: set ts=4 sw=4 et:

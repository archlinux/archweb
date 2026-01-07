from django.urls import path, re_path

from devel import views

urlpatterns = [
    path('admin_log/', views.admin_log),
    re_path(r'^admin_log/(?P<username>.*)/$', views.admin_log),
    path('clock/', views.clock, name='devel-clocks'),
    path('tier0mirror/', views.tier0_mirror, name='tier0-mirror'),
    path('mirrorauth/', views.tier0_mirror_auth, name='tier0-mirror-atuh'),
    path('', views.index, name='devel-index'),
    path('stats/', views.stats, name='devel-stats'),
    path('newuser/', views.new_user_form),
    path('profile/', views.change_profile),
    re_path(r'^reports/(?P<report_name>.*)/(?P<username>.*)/$', views.report),
    re_path(r'^reports/(?P<report_name>.*)/$', views.report),
]

# vim: set ts=4 sw=4 et:

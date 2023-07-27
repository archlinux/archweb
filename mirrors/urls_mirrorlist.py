from django.urls import re_path, path
from mirrors.views import mirrorlist as views

urlpatterns = [
    path('', views.generate_mirrorlist, name='mirrorlist'),
    path('submit/', views.submit_mirror, name='mirrorsubmit'),
    re_path(r'^all/$', views.find_mirrors, {'countries': ['all']}),
    re_path(r'^all/(?P<protocol>[A-z]+)/$', views.find_mirrors_simple, name='mirrorlist_simple')
]

# vim: set ts=4 sw=4 et:

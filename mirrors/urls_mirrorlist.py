from django.conf.urls import url

from mirrors.views import mirrorlist as views

urlpatterns = [
    url(r'^$', views.generate_mirrorlist, name='mirrorlist'),
    url(r'^all/$', views.find_mirrors, {'countries': ['all']}),
    url(r'^all/(?P<protocol>[A-z]+)/$', views.find_mirrors_simple, name='mirrorlist_simple')
]

# vim: set ts=4 sw=4 et:

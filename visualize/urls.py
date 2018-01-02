from django.conf.urls import url

from visualize import views


urlpatterns = [
    url(r'^$',          views.index,   name='visualize-index'),
    url(r'^by_arch/$',  views.by_arch, name='visualize-byarch'),
    url(r'^by_repo/$',  views.by_repo, name='visualize-byrepo'),
]

# vim: set ts=4 sw=4 et:

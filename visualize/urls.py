from django.urls import re_path
from visualize import views


urlpatterns = [
    re_path(r'^$',          views.index,   name='visualize-index'),
    re_path(r'^by_arch/$',  views.by_arch, name='visualize-byarch'),
    re_path(r'^by_repo/$',  views.by_repo, name='visualize-byrepo'),
]

# vim: set ts=4 sw=4 et:

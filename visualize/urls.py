from django.urls import path

from visualize import views

urlpatterns = [
    path('',          views.index,   name='visualize-index'),
    path('by_arch/',  views.by_arch, name='visualize-byarch'),
    path('by_repo/',  views.by_repo, name='visualize-byrepo'),
]

# vim: set ts=4 sw=4 et:

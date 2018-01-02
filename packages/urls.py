from django.conf.urls import include, url

from .views.search import SearchListView
from packages import views


package_patterns = [
    url(r'^$', views.details),
    url(r'^json/$', views.details_json),
    url(r'^files/$', views.files),
    url(r'^files/json/$', views.files_json),
    url(r'^flag/$', views.flag),
    url(r'^flag/done/$', views.flag_confirmed, name='package-flag-confirmed'),
    url(r'^unflag/$', views.unflag),
    url(r'^unflag/all/$', views.unflag_all),
    url(r'^signoff/$', views.signoff_package),
    url(r'^signoff/revoke/$', views.signoff_package, {'revoke': True}),
    url(r'^signoff/options/$', views.signoff_options),
    url(r'^download/$', views.download),
]

urlpatterns = [
    url(r'^flaghelp/$', views.flaghelp),
    url(r'^signoffs/$', views.signoffs, name='package-signoffs'),
    url(r'^signoffs/json/$', views.signoffs_json, name='package-signoffs-json'),
    url(r'^update/$', views.update),

    url(r'^$', SearchListView.as_view(), name='packages-search'),
    url(r'^search/json/$', views.search_json),

    url(r'^differences/$', views.arch_differences, name='packages-differences'),
    url(r'^stale_relations/$', views.stale_relations),
    url(r'^stale_relations/update/$', views.stale_relations_update),

    url(r'^(?P<name>[^ /]+)/$', views.details),
    url(r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[^ /]+)/$', views.details),
    # canonical package url. subviews defined above
    url(r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/', include(package_patterns)),
]

# vim: set ts=4 sw=4 et:

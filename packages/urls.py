from django.conf.urls import include, url

from packages import views
from packages.views import display, flag, signoff, search


package_patterns = [
    url(r'^$', display.details),
    url(r'^json/$', display.details_json),
    url(r'^files/$', display.files),
    url(r'^files/json/$', display.files_json),
    url(r'^flag/$', flag.flag),
    url(r'^flag/done/$', flag.flag_confirmed, name='package-flag-confirmed'),
    url(r'^unflag/$', flag.unflag),
    url(r'^unflag/all/$', flag.unflag_all),
    url(r'^signoff/$', signoff.signoff_package),
    url(r'^signoff/revoke/$', signoff.signoff_package, {'revoke': True}),
    url(r'^signoff/options/$', signoff.signoff_options),
    url(r'^download/$', display.download),
]

urlpatterns = [
    url(r'^flaghelp/$', flag.flaghelp),
    url(r'^signoffs/$', signoff.signoffs, name='package-signoffs'),
    url(r'^signoffs/json/$', signoff.signoffs_json, name='package-signoffs-json'),
    url(r'^update/$', views.update),

    url(r'^$', search.SearchListView.as_view(), name='packages-search'),
    url(r'^search/json/$', search.search_json),

    url(r'^differences/$', views.arch_differences, name='packages-differences'),
    url(r'^stale_relations/$', views.stale_relations),
    url(r'^stale_relations/update/$', views.stale_relations_update),

    url(r'^(?P<name>[^ /]+)/$', display.details),
    url(r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[^ /]+)/$', display.details),
    # canonical package url. subviews defined above
    url(r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/', include(package_patterns)),
]

# vim: set ts=4 sw=4 et:

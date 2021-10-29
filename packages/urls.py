from django.conf.urls import include
from django.urls import re_path
from packages import views
from packages.views import display, flag, signoff, search


package_patterns = [
    re_path(r'^$', display.details),
    re_path(r'^json/$', display.details_json),
    re_path(r'^files/$', display.files),
    re_path(r'^files/json/$', display.files_json),
    re_path(r'^flag/$', flag.flag),
    re_path(r'^flag/done/$', flag.flag_confirmed, name='package-flag-confirmed'),
    re_path(r'^unflag/$', flag.unflag),
    re_path(r'^unflag/all/$', flag.unflag_all),
    re_path(r'^signoff/$', signoff.signoff_package),
    re_path(r'^signoff/revoke/$', signoff.signoff_package, {'revoke': True}),
    re_path(r'^signoff/options/$', signoff.signoff_options),
    re_path(r'^download/$', display.download),
    re_path(r'^download.sig/$', display.download, {'sig': True}),
    re_path(r'^sonames/$', display.sonames),
    re_path(r'^sonames/json/$', display.sonames_json),
]

urlpatterns = [
    re_path(r'^flaghelp/$', flag.flaghelp),
    re_path(r'^signoffs/$', signoff.signoffs, name='package-signoffs'),
    re_path(r'^signoffs/json/$', signoff.signoffs_json, name='package-signoffs-json'),
    re_path(r'^update/$', views.update),
    re_path(r'^sonames$', views.sonames),

    re_path(r'^$', search.SearchListView.as_view(), name='packages-search'),
    re_path(r'^search/json/$', search.search_json),

    re_path(r'^differences/$', views.arch_differences, name='packages-differences'),
    re_path(r'^stale_relations/$', views.stale_relations),
    re_path(r'^stale_relations/update/$', views.stale_relations_update),

    re_path(r'^(?P<name>[^ /]+)/$', display.details),
    re_path(r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[^ /]+)/$', display.details),
    # canonical package url. subviews defined above
    re_path(r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/', include(package_patterns)),
]

# vim: set ts=4 sw=4 et:

from django.conf.urls import include
from django.urls import path, re_path

from packages import views
from packages.views import display, flag, search, signoff

package_patterns = [
    path('', display.details),
    path('json/', display.details_json),
    path('files/', display.files),
    path('files/json/', display.files_json),
    path('flag/', flag.flag),
    path('flag/done/', flag.flag_confirmed, name='package-flag-confirmed'),
    path('unflag/', flag.unflag),
    path('unflag/all/', flag.unflag_all),
    path('signoff/', signoff.signoff_package),
    path('signoff/revoke/', signoff.signoff_package, {'revoke': True}),
    path('signoff/options/', signoff.signoff_options),
    path('download/', display.download),
    path('download.sig/', display.download, {'sig': True}),
    path('sonames/', display.sonames),
    path('sonames/json/', display.sonames_json),
]

urlpatterns = [
    path('flaghelp/', flag.flaghelp),
    path('signoffs/', signoff.signoffs, name='package-signoffs'),
    path('signoffs/json/', signoff.signoffs_json, name='package-signoffs-json'),
    path('update/', views.update),
    path('sonames', views.sonames),
    path('pkgbase-maintainer', views.pkgbase_mapping),

    path('', search.SearchListView.as_view(), name='packages-search'),
    path('search/json/', search.search_json),

    path('differences/', views.arch_differences, name='packages-differences'),
    path('stale_relations/', views.stale_relations),
    path('stale_relations/update/', views.stale_relations_update),

    re_path(r'^(?P<name>[^ /]+)/$', display.details),
    re_path(r'^(?P<repo>[A-z0-9\-]+)/(?P<name>[^ /]+)/$', display.details),
    # canonical package url. subviews defined above
    re_path(r'^(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/', include(package_patterns)),
]

# vim: set ts=4 sw=4 et:

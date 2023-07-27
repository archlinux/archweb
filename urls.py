from django.urls import include, path, re_path
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.contrib.auth import views as auth_views
from django.conf import settings

from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from feeds import PackageFeed, NewsFeed, ReleaseFeed, PackageUpdatesFeed, PlanetFeed
import sitemaps

import devel.urls
import mirrors.urls
import mirrors.urls_mirrorlist
import news.urls
import packages.urls
import packages.urls_groups
import packages.views
import planet.views
import public.views
import releng.urls
import todolists.urls
import visualize.urls

our_sitemaps = {
    'base':           sitemaps.BaseSitemap,
    'news':           sitemaps.NewsSitemap,
    'packages':       sitemaps.PackagesSitemap,
    'package-files':  sitemaps.PackageFilesSitemap,
    'package-groups': sitemaps.PackageGroupsSitemap,
    'split-packages': sitemaps.SplitPackagesSitemap,
    'releases':       sitemaps.ReleasesSitemap,
    'todolists':      sitemaps.TodolistSitemap,
}

news_sitemaps = {'news': sitemaps.RecentNewsSitemap}

urlpatterns = []

# Public pages
urlpatterns.extend([
    path('', public.views.index, name='index'),
    path('about/', TemplateView.as_view(template_name='public/about.html'), name='page-about'),
    path('art/',   TemplateView.as_view(template_name='public/art.html'), name='page-art'),
    path('donate/', public.views.donate, name='page-donate'),
    path('download/', public.views.download, name='page-download'),
    path('master-keys/', public.views.keys, name='page-keys'),
    path('master-keys/json/', public.views.keys_json, name='pgp-keys-json'),
    re_path(r'^people/(?P<slug>[-\w]+)/$', public.views.people, name='people'),
    path('planet/', planet.views.index, name='planet'),
])

# Feeds patterns, used below
feeds_patterns = [
    path('', public.views.feeds, name='feeds-list'),
    path('news/', cache_page(311)(NewsFeed())),
    path('packages/', cache_page(313)(PackageFeed())),
    re_path(r'^packages/(added|removed)/$', cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(added|removed)/(?P<arch>[A-z0-9]+)/$', cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(added|removed)/all/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(added|removed)/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
            cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(?P<arch>[A-z0-9]+)/$', cache_page(313)(PackageFeed())),
    re_path(r'^packages/all/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageFeed())),
    re_path(r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageFeed())),
    path('releases/', cache_page(317)(ReleaseFeed())),
    path('planet/', cache_page(317)(PlanetFeed()), name='planet-feed'),
]

# Old planet.archlinux.org redirects, to be removed once people have migrated.
urlpatterns.extend([
    path('planet/rss20.xml', cache_page(317)(PlanetFeed())),
    path('planet/atom.xml', cache_page(317)(PlanetFeed())),
])

# Includes and other remaining stuff
urlpatterns.extend([
    path('admin/', admin.site.urls),
    path('devel/', include(devel.urls)),
    path('feeds/', include(feeds_patterns)),
    path('groups/', include(packages.urls_groups)),
    path('mirrorlist/', include(mirrors.urls_mirrorlist)),
    path('mirrors/', include(mirrors.urls)),
    path('news/', include(news.urls)),
    path('packages/', include(packages.urls)),
    path('releng/', include(releng.urls)),
    path('todo/', include(todolists.urls)),
    path('visualize/', include(visualize.urls)),
    path('opensearch/packages/', packages.views.opensearch, name='opensearch-packages'),
    path('opensearch/packages/suggest', packages.views.opensearch_suggest, name='opensearch-packages-suggest'),
])

# Sitemaps
urlpatterns.extend([
    path('sitemap.xml', cache_page(1831)(sitemap_views.index),
         {'sitemaps': our_sitemaps, 'sitemap_url_name': 'sitemaps'}),
    re_path(r'^sitemap-(?P<section>.+)\.xml$', cache_page(1831)(sitemap_views.sitemap),
            {'sitemaps': our_sitemaps, 'template_name': 'sitemaps/sitemap.xml'},
            name='sitemaps'),
    path('news-sitemap.xml', cache_page(1831)(sitemap_views.sitemap),
         {'sitemaps': news_sitemaps, 'template_name': 'sitemaps/news_sitemap.xml'},
         name='news-sitemap'),
])

# Authentication
urlpatterns.extend([
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
])

# Captcha
urlpatterns.extend([
    path('captcha/', include('captcha.urls')),
])

# django-toolbar
if settings.DEBUG_TOOLBAR:  # pragma: no cover
    import debug_toolbar
    urlpatterns.extend([
        path('__debug__/', include(debug_toolbar.urls)),
    ])


# displays all archweb urls
def show_urls(urllist=urlpatterns, depth=0):  # pragma: no cover
    for entry in urllist:
        print("  " * depth, entry.regex.pattern)
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

# vim: set ts=4 sw=4 et:

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
    re_path(r'^$', public.views.index, name='index'),
    re_path(r'^about/$', TemplateView.as_view(template_name='public/about.html'), name='page-about'),
    re_path(r'^art/$',   TemplateView.as_view(template_name='public/art.html'), name='page-art'),
    re_path(r'^svn/$',   TemplateView.as_view(template_name='public/svn.html'), name='page-svn'),
    re_path(r'^donate/$', public.views.donate, name='page-donate'),
    re_path(r'^download/$', public.views.download, name='page-download'),
    re_path(r'^master-keys/$', public.views.keys, name='page-keys'),
    re_path(r'^master-keys/json/$', public.views.keys_json, name='pgp-keys-json'),
    re_path(r'^people/(?P<slug>[-\w]+)/$', public.views.people, name='people'),
    re_path(r'^planet/$', planet.views.index, name='planet'),
])

# Feeds patterns, used below
feeds_patterns = [
    re_path(r'^$', public.views.feeds, name='feeds-list'),
    re_path(r'^news/$', cache_page(311)(NewsFeed())),
    re_path(r'^packages/$', cache_page(313)(PackageFeed())),
    re_path(r'^packages/(added|removed)/$', cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(added|removed)/(?P<arch>[A-z0-9]+)/$', cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(added|removed)/all/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(added|removed)/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
        cache_page(313)(PackageUpdatesFeed())),
    re_path(r'^packages/(?P<arch>[A-z0-9]+)/$', cache_page(313)(PackageFeed())),
    re_path(r'^packages/all/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageFeed())),
    re_path(r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageFeed())),
    re_path(r'^releases/$', cache_page(317)(ReleaseFeed())),
    re_path(r'^planet/$', cache_page(317)(PlanetFeed()), name='planet-feed'),
]

# Old planet.archlinux.org redirects, to be removed once people have migrated.
urlpatterns.extend([
    re_path(r'^planet/rss20.xml$', cache_page(317)(PlanetFeed())),
    re_path(r'^planet/atom.xml$', cache_page(317)(PlanetFeed())),
])

# Includes and other remaining stuff
urlpatterns.extend([
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^devel/', include(devel.urls)),
    re_path(r'^feeds/', include(feeds_patterns)),
    re_path(r'^groups/', include(packages.urls_groups)),
    re_path(r'^mirrorlist/', include(mirrors.urls_mirrorlist)),
    re_path(r'^mirrors/', include(mirrors.urls)),
    re_path(r'^news/', include(news.urls)),
    re_path(r'^packages/', include(packages.urls)),
    re_path(r'^releng/', include(releng.urls)),
    re_path(r'^todo/', include(todolists.urls)),
    re_path(r'^visualize/', include(visualize.urls)),
    re_path(r'^opensearch/packages/$', packages.views.opensearch, name='opensearch-packages'),
    re_path(r'^opensearch/packages/suggest$', packages.views.opensearch_suggest, name='opensearch-packages-suggest'),
])

# Sitemaps
urlpatterns.extend([
    re_path(r'^sitemap.xml$', cache_page(1831)(sitemap_views.index),
        {'sitemaps': our_sitemaps, 'sitemap_url_name': 'sitemaps'}),
    re_path(r'^sitemap-(?P<section>.+)\.xml$', cache_page(1831)(sitemap_views.sitemap),
        {'sitemaps': our_sitemaps, 'template_name': 'sitemaps/sitemap.xml'},
        name='sitemaps'),
    re_path(r'^news-sitemap\.xml$', cache_page(1831)(sitemap_views.sitemap),
        {'sitemaps': news_sitemaps, 'template_name': 'sitemaps/news_sitemap.xml'},
        name='news-sitemap'),
])

# Authentication
urlpatterns.extend([
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
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

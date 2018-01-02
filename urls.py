from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.contrib.auth import views as auth_views

from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from feeds import PackageFeed, NewsFeed, ReleaseFeed
import sitemaps

import devel.urls
import mirrors.urls
import mirrors.urls_mirrorlist
import news.urls
import packages.urls
import packages.urls_groups
import public.views
import releng.urls
import retro.views
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
    url(r'^$', public.views.index, name='index'),
    url(r'^about/$', TemplateView.as_view(template_name='public/about.html'), name='page-about'),
    url(r'^art/$',   TemplateView.as_view(template_name='public/art.html'), name='page-art'),
    url(r'^svn/$',   TemplateView.as_view(template_name='public/svn.html'), name='page-svn'),
    url(r'^donate/$', public.views.donate, name='page-donate'),
    url(r'^download/$', public.views.download, name='page-download'),
    url(r'^master-keys/$', public.views.keys, name='page-keys'),
    url(r'^master-keys/json/$', public.views.keys_json, name='pgp-keys-json'),
    url(r'^people/(?P<slug>[-\w]+)/$', public.views.people, name='people'),
])

# Feeds patterns, used below
feeds_patterns = [
    url(r'^$', public.views.feeds, name='feeds-list'),
    url(r'^news/$', cache_page(311)(NewsFeed())),
    url(r'^packages/$', cache_page(313)(PackageFeed())),
    url(r'^packages/(?P<arch>[A-z0-9]+)/$', cache_page(313)(PackageFeed())),
    url(r'^packages/all/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageFeed())),
    url(r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$', cache_page(313)(PackageFeed())),
    url(r'^releases/$', cache_page(317)(ReleaseFeed())),
]

# Includes and other remaining stuff
urlpatterns.extend([
    url(r'^admin/',     include(admin.site.urls)),
    url(r'^devel/',     include(devel.urls)),
    url(r'^feeds/',     include(feeds_patterns)),
    url(r'^groups/',    include(packages.urls_groups)),
    url(r'^mirrorlist/',include(mirrors.urls_mirrorlist)),
    url(r'^mirrors/',   include(mirrors.urls)),
    url(r'^news/',      include(news.urls)),
    url(r'^packages/',  include(packages.urls)),
    url(r'^releng/',    include(releng.urls)),
    url(r'^todo/',      include(todolists.urls)),
    url(r'^visualize/', include(visualize.urls)),
    url(r'^opensearch/packages/$', packages.views.opensearch, name='opensearch-packages'),
    url(r'^opensearch/packages/suggest$', packages.views.opensearch_suggest, name='opensearch-packages-suggest'),
])

# Retro home page views
urlpatterns.extend([
    url(r'^retro/(?P<year>[0-9]{4})/$', retro.views.retro_homepage, name='retro-homepage'),
])

# Sitemaps
urlpatterns.extend([
    url(r'^sitemap.xml$', cache_page(1831)(sitemap_views.index),
        {'sitemaps': our_sitemaps, 'sitemap_url_name': 'sitemaps'}),
    url(r'^sitemap-(?P<section>.+)\.xml$', cache_page(1831)(sitemap_views.sitemap),
        {'sitemaps': our_sitemaps, 'template_name': 'sitemaps/sitemap.xml'},
        name='sitemaps'),
    url(r'^news-sitemap\.xml$', cache_page(1831)(sitemap_views.sitemap),
        {'sitemaps': news_sitemaps, 'template_name': 'sitemaps/news_sitemap.xml'},
        name='news-sitemap'),
])

# Authentication
urlpatterns.extend([
    url(r'^login/$', auth_views.login, {'template_name': 'registration/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'registration/logout.html'}, name='logout'),
])


def show_urls(urllist=urlpatterns, depth=0):
    for entry in urllist:
        print("  " * depth, entry.regex.pattern)
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

# vim: set ts=4 sw=4 et:

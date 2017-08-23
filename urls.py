from django.conf.urls import include, patterns
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views

from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from feeds import PackageFeed, NewsFeed, ReleaseFeed
import sitemaps

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
urlpatterns += patterns('public.views',
    (r'^$', 'index', {}, 'index'),
    (r'^about/$', TemplateView.as_view(template_name='public/about.html'),
        {}, 'page-about'),
    (r'^art/$',   TemplateView.as_view(template_name='public/art.html'),
        {}, 'page-art'),
    (r'^svn/$',   TemplateView.as_view(template_name='public/svn.html'),
        {}, 'page-svn'),
    (r'^donate/$',       'donate',   {}, 'page-donate'),
    (r'^download/$',     'download', {}, 'page-download'),
    (r'^master-keys/$',  'keys',     {}, 'page-keys'),
    (r'^master-keys/json/$', 'keys_json', {}, 'pgp-keys-json'),
    (r'^people/(?P<slug>[-\w]+)/$', 'people', {}, 'people'),
)

# Feeds patterns, used below
feeds_patterns = patterns('',
    (r'^$',          'public.views.feeds', {}, 'feeds-list'),
    (r'^news/$',     cache_page(311)(NewsFeed())),
    (r'^packages/$', cache_page(313)(PackageFeed())),
    (r'^packages/(?P<arch>[A-z0-9]+)/$',
        cache_page(313)(PackageFeed())),
    (r'^packages/all/(?P<repo>[A-z0-9\-]+)/$',
        cache_page(313)(PackageFeed())),
    (r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
        cache_page(313)(PackageFeed())),
    (r'^releases/$', cache_page(317)(ReleaseFeed())),
)

# Includes and other remaining stuff
urlpatterns += patterns('',
    (r'^admin/',     include(admin.site.urls)),
    (r'^devel/',     include('devel.urls')),
    (r'^feeds/',     include(feeds_patterns)),
    (r'^groups/',    include('packages.urls_groups')),
    (r'^mirrorlist/',include('mirrors.urls_mirrorlist')),
    (r'^mirrors/',   include('mirrors.urls')),
    (r'^news/',      include('news.urls')),
    (r'^packages/',  include('packages.urls')),
    (r'^releng/',    include('releng.urls')),
    (r'^todo/',      include('todolists.urls')),
    (r'^visualize/', include('visualize.urls')),
    (r'^opensearch/packages/$', 'packages.views.opensearch',
        {}, 'opensearch-packages'),
    (r'^opensearch/packages/suggest$', 'packages.views.opensearch_suggest',
        {}, 'opensearch-packages-suggest'),
)

# Retro home page views
urlpatterns += patterns('retro.views',
    (r'^retro/(?P<year>[0-9]{4})/$', 'retro_homepage', {}, 'retro-homepage'),
)

# Sitemaps
urlpatterns += patterns('',
    (r'^sitemap.xml$',
        cache_page(1831)(sitemap_views.index),
        {'sitemaps': our_sitemaps, 'sitemap_url_name': 'sitemaps'}),
    (r'^sitemap-(?P<section>.+)\.xml$',
        cache_page(1831)(sitemap_views.sitemap),
        {'sitemaps': our_sitemaps, 'template_name': 'sitemaps/sitemap.xml'},
        'sitemaps'),
    (r'^news-sitemap\.xml$',
        cache_page(1831)(sitemap_views.sitemap),
        {'sitemaps': news_sitemaps, 'template_name': 'sitemaps/news_sitemap.xml'},
        'news-sitemap'),
)

# Authentication
urlpatterns += patterns('django.contrib.auth.views',
    (r'^login/$', 'login', {'template_name': 'registration/login.html'}, 'login'),
    (r'^logout/$', 'logout', {'template_name': 'registration/logout.html'}, 'logout'),
)


def show_urls(urllist=urlpatterns, depth=0):
    for entry in urllist:
        print("  " * depth, entry.regex.pattern)
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

# vim: set ts=4 sw=4 et:

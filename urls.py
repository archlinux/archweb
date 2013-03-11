from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views

from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, RedirectView

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
}

admin.autodiscover()
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
    (r'^developers/$',   'userlist', { 'user_type':'devs' },    'page-devs'),
    (r'^trustedusers/$', 'userlist', { 'user_type':'tus' },     'page-tus'),
    (r'^fellows/$',      'userlist', { 'user_type':'fellows' }, 'page-fellows'),
    (r'^donate/$',       'donate',   {}, 'page-donate'),
    (r'^download/$',     'download', {}, 'page-download'),
    (r'^master-keys/$',  'keys',     {}, 'page-keys'),
    (r'^master-keys/json/$', 'keys_json', {}, 'pgp-keys-json'),
)

# Feeds patterns, used below
feeds_patterns = patterns('',
    (r'^$',          'public.views.feeds', {}, 'feeds-list'),
    (r'^news/$',     cache_page(300)(NewsFeed())),
    (r'^packages/$', cache_page(300)(PackageFeed())),
    (r'^packages/(?P<arch>[A-z0-9]+)/$',
        cache_page(300)(PackageFeed())),
    (r'^packages/all/(?P<repo>[A-z0-9\-]+)/$',
        cache_page(300)(PackageFeed())),
    (r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
        cache_page(300)(PackageFeed())),
    (r'^releases/$', cache_page(300)(ReleaseFeed())),
)

# Includes and other remaining stuff
urlpatterns += patterns('',
    # cache this static JS resource for 1 week rather than default 5 minutes
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
        cache_page(1800)(sitemap_views.index),
        {'sitemaps': our_sitemaps, 'sitemap_url_name': 'sitemaps'}),
    (r'^sitemap-(?P<section>.+)\.xml$',
        cache_page(1800)(sitemap_views.sitemap),
        {'sitemaps': our_sitemaps}, 'sitemaps'),
)

# Authentication / Admin
urlpatterns += patterns('django.contrib.auth.views',
    (r'^login/$',           'login',  {
        'template_name': 'registration/login.html'}),
    (r'^logout/$',          'logout', {
        'template_name': 'registration/logout.html'}),
)

# Redirects for older known pages we see in the logs
legacy_urls = (
    ('^about.php',     '/about/'),
    ('^changelog.php', '/packages/?sort=-last_update'),
    ('^devs.php',      '/developers/'),
    ('^donations.php', '/donate/'),
    ('^download.php',  '/download/'),
    ('^index.php',     '/'),
    ('^logos.php',     '/art/'),
    ('^news.php',      '/news/'),
    ('^packages.php',  '/packages/'),
    ('^people.php',    '/developers/'),
    ('^todolists/$',   '/todo/'),

    ('^docs/en/guide/install/arch-install-guide.html',
        'https://wiki.archlinux.org/index.php/Installation_Guide'),
    ('^docs/en/',
        'https://wiki.archlinux.org/'),
    ('^docs/',
        'https://wiki.archlinux.org/'),
)

urlpatterns += [url(old_url, RedirectView.as_view(url=new_url))
        for old_url, new_url in legacy_urls]


def show_urls(urllist=urlpatterns, depth=0):
    for entry in urllist:
        print "  " * depth, entry.regex.pattern
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)

# vim: set ts=4 sw=4 et:

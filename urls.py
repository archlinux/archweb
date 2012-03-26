import os.path

# Stupid Django. Don't remove these "unused" handler imports
from django.conf.urls import handler500, handler404, include, patterns
from django.conf import settings
from django.contrib import admin

from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.views.i18n import null_javascript_catalog

from feeds import PackageFeed, NewsFeed
import sitemaps

our_sitemaps = {
    'base':           sitemaps.BaseSitemap,
    'news':           sitemaps.NewsSitemap,
    'packages':       sitemaps.PackagesSitemap,
    'package-files':  sitemaps.PackageFilesSitemap,
    'package-groups': sitemaps.PackageGroupsSitemap,
    'split-packages': sitemaps.SplitPackagesSitemap,
}

admin.autodiscover()
urlpatterns = []

# Feeds patterns, used later
feeds_patterns = patterns('',
    (r'^$',          'public.views.feeds', {}, 'feeds-list'),
    (r'^news/$',     cache_page(300)(NewsFeed())),
    (r'^packages/$', cache_page(300)(PackageFeed())),
    (r'^packages/(?P<arch>[A-z0-9]+)/$',
        cache_page(300)(PackageFeed())),
    (r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
        cache_page(300)(PackageFeed())),
)

# Sitemaps
urlpatterns += patterns('django.contrib.sitemaps.views',
    # Thanks Django, we can't cache these longer because of
    # https://code.djangoproject.com/ticket/2713
    (r'^sitemap.xml$', 'index',
        {'sitemaps': our_sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'sitemap',
        {'sitemaps': our_sitemaps}),
)

# Authentication / Admin
urlpatterns += patterns('django.contrib.auth.views',
    (r'^login/$',           'login',  {
        'template_name': 'registration/login.html'}),
    (r'^logout/$',          'logout', {
        'template_name': 'registration/logout.html'}),
)

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
)

urlpatterns += patterns('retro.views',
    (r'^retro/(?P<year>[0-9]{4})/$', 'retro_homepage', {}, 'retro-homepage'),
)

# Includes and other remaining stuff
urlpatterns += patterns('',
    # cache this static JS resource for 1 week rather than default 5 minutes
    (r'^jsi18n/$',   cache_page(604800)(null_javascript_catalog)),
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
    (r'^todolists/$','todolists.views.public_list'),
)

legacy_urls = (
    ('^about.php',     '/about/'),
    ('^changelog.php', '/packages/?sort=-last_update'),
    ('^download.php',  '/download/'),
    ('^index.php',     '/'),
    ('^logos.php',     '/art/'),
    ('^news.php',      '/news/'),
)

for old_url, new_url in legacy_urls:
    urlpatterns += patterns('django.views.generic.simple',
            (old_url, 'redirect_to', {'url': new_url}))

# vim: set ts=4 sw=4 et:

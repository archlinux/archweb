import os.path

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from django.views.generic import TemplateView

from feeds import PackageFeed, NewsFeed
import sitemaps

sitemaps = {
    'news':           sitemaps.NewsSitemap,
    'packages':       sitemaps.PackagesSitemap,
    'package-files':  sitemaps.PackageFilesSitemap,
    'package-groups': sitemaps.PackageGroupsSitemap,
}

admin.autodiscover()
urlpatterns = []

# Feeds patterns, used later
feeds_patterns = patterns('',
    (r'^$',          'public.views.feeds', {}, 'feeds-list'),
    (r'^news/$',     NewsFeed()),
    (r'^packages/$', PackageFeed()),
    (r'^packages/(?P<arch>[A-z0-9]+)/$',
        PackageFeed()),
    (r'^packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
        PackageFeed()),
)

# Sitemaps
urlpatterns += patterns('django.contrib.sitemaps.views',
    (r'^sitemap.xml$', 'index',
        {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'sitemap',
        {'sitemaps': sitemaps}),
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
    (r'^developers/$',   'userlist', { 'type':'devs' },    'page-devs'),
    (r'^trustedusers/$', 'userlist', { 'type':'tus' },     'page-tus'),
    (r'^fellows/$',      'userlist', { 'type':'fellows' }, 'page-fellows'),
    (r'^donate/$',       'donate',   {}, 'page-donate'),
    (r'^download/$',     'download', {}, 'page-download'),
)

# Includes and other remaining stuff
urlpatterns += patterns('',
    (r'^jsi18n/$',   'django.views.i18n.null_javascript_catalog'),
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
    (r'^opensearch/packages/$', 'packages.views.opensearch',
        {}, 'opensearch-packages'),
    (r'^todolists/$','todolists.views.public_list'),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.DEPLOY_PATH, 'media')}))

# vim: set ts=4 sw=4 et:

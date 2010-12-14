from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from django.views.generic.simple import direct_to_template

from feeds import PackageFeed, NewsFeed
import sitemaps

sitemaps = {
    'news':           sitemaps.NewsSitemap,
    'packages':       sitemaps.PackagesSitemap,
    'package-files':  sitemaps.PackageFilesSitemap,
    'package-groups': sitemaps.PackageGroupsSitemap,
}

admin.autodiscover()

urlpatterns = patterns('packages.views',
    (r'^groups/$', 'groups'),
    (r'^groups/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'group_details'),

    (r'^opensearch/packages/$', 'opensearch', {}, 'opensearch-packages'),
)

urlpatterns += patterns('todolists.views',
    (r'^todolists/$',                  'public_list'),
)

urlpatterns += patterns('mirrors.views',
    (r'^mirrors/status/$',      'status',  {}, 'mirror-status'),
    (r'^mirrors/status/json/$', 'status_json',  {}, 'mirror-status-json'),

    (r'^mirrors/$',        'mirrors', {}, 'mirrors-list'),
    (r'^mirrors/(?P<name>[\.\-\w]+)/$', 'mirror_details'),

    (r'^mirrorlist/$',         'generate_mirrorlist', {}, 'mirrorlist'),
    (r'^mirrorlist/all/$',     'find_mirrors', {'countries': ['all']}),
    (r'^mirrorlist/all/ftp/$', 'find_mirrors',
        {'countries': ['all'], 'protocols': ['ftp']}),
    (r'^mirrorlist/all/http/$', 'find_mirrors',
        {'countries': ['all'], 'protocols': ['http']}),
)

# Feeds and sitemaps
urlpatterns += patterns('',
    (r'^feeds/$', 'public.views.feeds', {}, 'feeds-list'),
    (r'^feeds/news/$', NewsFeed()),
    (r'^feeds/packages/$', PackageFeed()),
    (r'^feeds/packages/(?P<arch>[A-z0-9]+)/$',
        PackageFeed()),
    (r'^feeds/packages/(?P<arch>[A-z0-9]+)/(?P<repo>[A-z0-9\-]+)/$',
        PackageFeed()),
    (r'^sitemap.xml$', 'django.contrib.sitemaps.views.index',
        {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),
)

# Authentication / Admin
urlpatterns += patterns('django.contrib.auth.views',
    (r'^login/$',           'login',  {
        'template_name': 'registration/login.html'}),
    (r'^accounts/login/$',  'login',  {
        'template_name': 'registration/login.html'}),
    (r'^logout/$',          'logout', {
        'template_name': 'registration/logout.html'}),
    (r'^accounts/logout/$', 'logout', {
        'template_name': 'registration/logout.html'}),
)

# Public pages
urlpatterns += patterns('public.views',
    (r'^$', 'index', {}, 'index'),
    (r'^about/$', direct_to_template, {'template': 'public/about.html'}, 'page-about'),
    (r'^art/$', direct_to_template, {'template': 'public/art.html'}, 'page-art'),
    (r'^svn/$', direct_to_template, {'template': 'public/svn.html'}, 'page-svn'),
    (r'^developers/$',   'userlist', { 'type':'Developers' }, 'page-devs'),
    (r'^trustedusers/$', 'userlist', { 'type':'Trusted Users' }, 'page-tus'),
    (r'^fellows/$',      'userlist', { 'type':'Fellows' }, 'page-fellows'),
    (r'^donate/$',       'donate', {}, 'page-donate'),
    (r'^download/$',     'download', {}, 'page-download'),
)

# Includes and other remaining stuff
urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^jsi18n/$', 'django.views.i18n.null_javascript_catalog'),

    (r'^devel/',     include('devel.urls')),
    (r'^news/',      include('news.urls')),
    (r'^packages/',  include('packages.urls')),
    (r'^todo/',      include('todolists.urls')),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', 
            {'document_root': settings.DEPLOY_PATH+'/media'}))

# vim: set ts=4 sw=4 et:

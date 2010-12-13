from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from django.views.generic.simple import direct_to_template

from main.models import Todolist
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
    (r'^packages/flaghelp/$', 'flaghelp'),
    (r'^packages/signoffs/$', 'signoffs'),
    (r'^packages/signoff_package/(?P<arch>[A-z0-9]+)/(?P<pkgname>[A-z0-9\-+.]+)/$',
        'signoff_package'),
    (r'^packages/update/$',   'update'),

    # Preference is for the packages/ url below, but search is kept
    # because other projects link to it
    (r'^packages/search/$',               'search'),
    (r'^packages/search/(?P<page>\d+)/$', 'search'),
    (r'^packages/$',                      'search'),
    (r'^packages/(?P<page>\d+)/$',        'search'),

    (r'^packages/differences/$',          'arch_differences'),

    (r'^packages/(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/files/$',
        'files'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/maintainer/$',
        'getmaintainer'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/flag/$',
        'flag'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/unflag/$',
        'unflag'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/download/$',
        'download'),

    (r'^groups/$', 'groups'),
    (r'^groups/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'group_details'),

    (r'^opensearch/packages/$', 'opensearch', {}, 'opensearch-packages'),
)

urlpatterns += patterns('todolists.views',
    (r'^todo/$',                       'list'),
    (r'^todo/(\d+)/$',                 'view'),
    (r'^todo/add/$',                   'add'),
    (r'^todo/edit/(?P<list_id>\d+)/$', 'edit'),
    (r'^todo/flag/(\d+)/(\d+)/$',      'flag'),
    (r'^todo/delete/(?P<object_id>\d+)/$',
        'delete_todolist'),

    (r'^todolists/$',                  'public_list'),
)

urlpatterns += patterns('news.views',
    (r'^news/add/$',                     'add'),
    (r'^news/preview/$',                 'preview'),
    # old news URLs, permanent redirect view so we don't break all links
    (r'^news/(?P<object_id>\d+)/$',      'view_redirect'),
    (r'^news/(?P<slug>[-\w]+)/$',        'view'),
    (r'^news/(?P<slug>[-\w]+)/edit/$',   'edit'),
    (r'^news/(?P<slug>[-\w]+)/delete/$', 'delete'),
    (r'^news/$',                         'news_list', {}, 'news-list'),
)

urlpatterns += patterns('mirrors.views',
    (r'^mirrors/$',        'mirrors', {}, 'mirrors-list'),
    (r'^mirrors/(?P<name>[\.\-\w]+)/$', 'mirror_details'),

    (r'^mirrors/status/$',      'status',  {}, 'mirror-status'),
    (r'^mirrors/status/json/$', 'status_json',  {}, 'mirror-status-json'),

    (r'^mirrorlist/$',         'generate_mirrorlist', {}, 'mirrorlist'),
    (r'^mirrorlist/all/$',     'find_mirrors', {'countries': ['all']}),
    (r'^mirrorlist/all/ftp/$', 'find_mirrors',
        {'countries': ['all'], 'protocols': ['ftp']}),
    (r'^mirrorlist/all/http/$', 'find_mirrors',
        {'countries': ['all'], 'protocols': ['http']}),
)

urlpatterns += patterns('devel.views',
    (r'^devel/$',          'index'),
    (r'^devel/notify/$',   'change_notify'),
    (r'^devel/profile/$',  'change_profile'),
    (r'^devel/newuser/$',  'new_user_form'),
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

# (mostly) Static Pages
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

urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^jsi18n/$', 'django.views.i18n.null_javascript_catalog'),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', 
            {'document_root': settings.DEPLOY_PATH+'/media'}))

# vim: set ts=4 sw=4 et:

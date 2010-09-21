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

urlpatterns = patterns('',
    (r'^packages/flaghelp/$', 'packages.views.flaghelp'),
    (r'^packages/signoffs/$', 'packages.views.signoffs'),
    (r'^packages/signoff_package/(?P<arch>[A-z0-9]+)/(?P<pkgname>[A-z0-9\-+.]+)/$',
        'packages.views.signoff_package'),
    (r'^packages/update/$',   'packages.views.update'),

    # Preference is for the packages/ url below, but search is kept
    # because other projects link to it
    (r'^packages/search/$',          'packages.views.search'),
    (r'^packages/search/(?P<page>\d+)/$', 'packages.views.search'),
    (r'^packages/differences/$',     'packages.views.arch_differences'),
    (r'^packages/$',                     'packages.views.search'),
    (r'^packages/(?P<page>\d+)/$',        'packages.views.search'),

    (r'^packages/(?P<name>[A-z0-9\-+.]+)/$',
        'packages.views.details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'packages.views.details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'packages.views.details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/files/$',
        'packages.views.files'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/maintainer/$',
        'packages.views.getmaintainer'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/flag/$',
        'packages.views.flag'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/unflag/$',
        'packages.views.unflag'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/download/$',
        'packages.views.download'),

    (r'^groups/$', 'packages.views.groups'),
    (r'^groups/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'packages.views.group_details'),

    (r'^todo/(\d+)/$',              'todolists.views.view'),
    (r'^todo/add/$',                'todolists.views.add'),
    (r'^todo/edit/(?P<list_id>\d+)/$',  'todolists.views.edit'),
    (r'^todo/flag/(\d+)/(\d+)/$',   'todolists.views.flag'),
    (r'^todo/delete/(?P<object_id>\d+)/$',
        'todolists.views.delete_todolist'),
    (r'^todo/$',                    'todolists.views.list'),
    (r'^todolists/$',               'todolists.views.public_list'),

    (r'^news/add/$',                     'news.views.add'),
    (r'^news/preview/$',                 'news.views.preview'),
    # old news URLs, permanent redirect view so we don't break all links
    (r'^news/(?P<object_id>\d+)/$',      'news.views.view_redirect'),
    (r'^news/(?P<slug>[-\w]+)/$',        'news.views.view'),
    (r'^news/(?P<slug>[-\w]+)/edit/$',   'news.views.edit'),
    (r'^news/(?P<slug>[-\w]+)/delete/$', 'news.views.delete'),
    (r'^news/$',                         'news.views.news_list', {}, 'news-list'),

    (r'^mirrors/$',        'devel.views.mirrorlist', {}, 'mirrors-list'),
    (r'^mirrors/status/$', 'mirrors.views.status', {}, 'mirror-status'),

    (r'^mirrorlist/$', 'mirrors.views.generate_mirrorlist', {}, 'mirrorlist'),
    (r'^mirrorlist/all/$', 'mirrors.views.find_mirrors', {'countries': ['all']}),
    (r'^mirrorlist/all/ftp/$', 'mirrors.views.find_mirrors',
        {'countries': ['all'], 'protocols': ['ftp']}),
    (r'^mirrorlist/all/http/$', 'mirrors.views.find_mirrors',
        {'countries': ['all'], 'protocols': ['http']}),

    (r'^devel/$',          'devel.views.index'),
    (r'^devel/notify/$',   'devel.views.change_notify'),
    (r'^devel/profile/$',  'devel.views.change_profile'),

    (r'^devel/newuser/$', 'devel.views.new_user_form'),

# Feeds and sitemaps
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

# Authentication / Admin
    (r'^login/$',           'django.contrib.auth.views.login',  {
        'template_name': 'registration/login.html'}),
    (r'^accounts/login/$',  'django.contrib.auth.views.login',  {
        'template_name': 'registration/login.html'}),
    (r'^logout/$',          'django.contrib.auth.views.logout', {
        'template_name': 'registration/logout.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {
        'template_name': 'registration/logout.html'}),
    (r'^admin/', include(admin.site.urls)),

# (mostly) Static Pages
    (r'^$', 'public.views.index', {}, 'index'),
    (r'^about/$', direct_to_template, {'template': 'public/about.html'}, 'page-about'),
    (r'^art/$', direct_to_template, {'template': 'public/art.html'}, 'page-art'),
    (r'^svn/$', direct_to_template, {'template': 'public/svn.html'}, 'page-svn'),
    (r'^developers/$',   'public.views.userlist', { 'type':'Developers' }, 'page-devs'),
    (r'^trustedusers/$', 'public.views.userlist', { 'type':'Trusted Users' }, 'page-tus'),
    (r'^fellows/$',      'public.views.userlist', { 'type':'Fellows' }, 'page-fellows'),
    (r'^donate/$', 'public.views.donate', {}, 'page-donate'),
    (r'^download/$', 'public.views.download', {}, 'page-download'),
    (r'^opensearch/packages/$', 'packages.views.opensearch', {}, 'opensearch-packages'),

# Some django internals we use
    (r'^jsi18n/$', 'django.views.i18n.null_javascript_catalog'),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', 
            {'document_root': settings.DEPLOY_PATH+'/media'}))

# vim: set ts=4 sw=4 et:

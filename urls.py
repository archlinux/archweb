from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from django.views.generic.create_update import delete_object
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import permission_required

from main.models import Todolist
from feeds import PackageFeed, NewsFeed
from sitemaps import NewsSitemap, PackagesSitemap, PackageFilesSitemap


feeds = {
    'news':     NewsFeed,
    'packages': PackageFeed,
}

sitemaps = {
    'news':          NewsSitemap,
    'packages':      PackagesSitemap,
    'package-files': PackageFilesSitemap,
}

admin.autodiscover()

urlpatterns = patterns('',
    (r'^packages/flag/(\d+)/$', 'packages.views.flag'),
    (r'^packages/flaghelp/$', 'packages.views.flaghelp'),
    (r'^packages/unflag/(\d+)/$',        'packages.views.unflag'),
    (r'^packages/signoffs/$',              'packages.views.signoffs'),
    (r'^packages/signoff_package/(?P<arch>[A-z0-9]+)/(?P<pkgname>[A-z0-9\-+.]+)/$',
        'packages.views.signoff_package'),
    (r'^packages/update/$',              'packages.views.update'),

    # Preference is for the packages/ url below, but search is kept
    # because other projects link to it
    (r'^packages/search/$',          'packages.views.search'),
    (r'^packages/search/(?P<page>\d+)/$', 'packages.views.search'),
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

    (r'^todo/(\d+)/$',              'todolists.views.view'),
    (r'^todo/add/$',                'todolists.views.add'),
    (r'^todo/edit/(?P<list_id>\d+)/$',  'todolists.views.edit'),
    (r'^todo/flag/(\d+)/(\d+)/$',   'todolists.views.flag'),
    (r'^todo/delete/(?P<object_id>\d+)/$',
        'todolists.views.delete_todolist'),
    (r'^todo/$',                    'todolists.views.list'),

    (r'^news/(\d+)/$',         'news.views.view'),
    (r'^news/add/$',           'news.views.add'),
    (r'^news/edit/(\d+)/$',    'news.views.edit'),
    (r'^news/delete/(\d+)/$',  'news.views.delete'),
    (r'^news/$',               'news.views.list'),

    (r'^mirrors/$',        'devel.views.mirrorlist'),

    (r'^mirrorlist/$', 'mirrors.views.choose'),
    (r'^mirrorlist/(?P<arch>[\S]+)/(?P<country>[A-z0-9 ]+)/$',
        'mirrors.views.generate'),
    (r'^mirrorlist/(?P<arch>[\S]+)/$',
        'mirrors.views.generate'),

    (r'^devel/$',          'devel.views.index'),
    (r'^devel/notify/$',   'devel.views.change_notify'),
    (r'^devel/profile/$',  'devel.views.change_profile'),

    (r'^devel/newuser/$', 'devel.views.new_user_form'),

# Feeds and sitemaps
    (r'^feeds/$', 'public.views.feeds'),
    (r'^feeds/(?P<url>.*)/$',
        'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
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
    (r'^admin/(.*)', admin.site.root),

# (mostly) Static Pages
    (r'^$', 'public.views.index'),
    (r'^about/$', direct_to_template, {'template': 'public/about.html'}),
    (r'^art/$', direct_to_template, {'template': 'public/art.html'}),
    (r'^svn/$', direct_to_template, {'template': 'public/svn.html'}),
    (r'^developers/$',   'public.views.userlist', { 'type':'Developers' }),
    (r'^trustedusers/$', 'public.views.userlist', { 'type':'Trusted Users' }),
    (r'^fellows/$',      'public.views.userlist', { 'type':'Fellows' }),
    (r'^donate/$', 'public.views.donate'),
    (r'^download/$', 'public.views.download'),
    (r'^irc/$', direct_to_template, {'template': 'public/irc.html'}),
    (r'^moreforums/$', 'public.views.moreforums'),
    (r'^projects/$', 'public.views.projects'),
    (r'^opensearch/packages/$', 'packages.views.opensearch'),

# Some django internals we use
    (r'^jsi18n/$', 'django.views.i18n.null_javascript_catalog'),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', 
            {'document_root': settings.DEPLOY_PATH+'/media'}))

# vim: set ts=4 sw=4 et:


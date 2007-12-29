from django.conf.urls.defaults import *
from django.conf import settings
from archweb_dev.news.models import News
from archweb_dev.feeds import PackageFeed, NewsFeed
from django.views.decorators.cache import cache_page

feeds = {
    'packages': PackageFeed,
    'news':     NewsFeed
}

urlpatterns = patterns('',
# Dynamic Stuff
    (r'^packages/flag/(\d+)/$',          'archweb_dev.packages.views.flag'),
    (r'^packages/flaghelp/$',            'archweb_dev.packages.views.flaghelp'),
    (r'^packages/unflag/(\d+)/$',        'archweb_dev.packages.views.unflag'),
    (r'^packages/files/(\d+)/$',         'archweb_dev.packages.views.files'),
    (r'^packages/search/$',              'archweb_dev.packages.views.search'),
    (r'^packages/search/([A-z0-9]+)/$',  'archweb_dev.packages.views.search'),
    (r'^packages/update/$',              'archweb_dev.packages.views.update'),
    (r'^packages/(?P<pkgid>\d+)/$',      'archweb_dev.packages.views.details'),
    (r'^packages/(?P<name>[A-z0-9]+)/$', 'archweb_dev.packages.views.details'),
    (r'^packages/(?P<repo>[A-z0-9]+)/(?P<name>[A-z0-9]+)/$', 'archweb_dev.packages.views.details'),
    (r'^packages/$',                     'archweb_dev.packages.views.search'),

    (r'^todo/(\d+)/$',            'archweb_dev.todolists.views.view'),
    (r'^todo/add/$',              'archweb_dev.todolists.views.add'),
    (r'^todo/flag/(\d+)/(\d+)/$', 'archweb_dev.todolists.views.flag'),
    (r'^todo/$',                  'archweb_dev.todolists.views.list'),

    (r'^news/(\d+)/$',         'archweb_dev.news.views.view'),
    (r'^news/add/$',           'archweb_dev.news.views.add'),
    (r'^news/edit/(\d+)/$',    'archweb_dev.news.views.edit'),
    (r'^news/delete/(\d+)/$',  'archweb_dev.news.views.delete'),
    (r'^news/$',               'archweb_dev.news.views.list'),

    (r'^devel/$',          'archweb_dev.devel.views.index'),
    (r'^devel/notify/$',   'archweb_dev.devel.views.change_notify'),
    (r'^devel/profile/$',  'archweb_dev.devel.views.change_profile'),
    (r'^devel/guide/$',    'archweb_dev.devel.views.guide'),

    (r'^wiki/([A-Z]+[A-z0-9 :/-]+)/$',      'archweb_dev.wiki.views.page'),
    (r'^wiki/edit/([A-Z]+[A-z0-9 :/-]+)/$', 'archweb_dev.wiki.views.edit'),
    (r'^wiki/delete/$',                     'archweb_dev.wiki.views.delete'),
    (r'^wiki/index/$',                      'archweb_dev.wiki.views.index'),
    (r'^wiki/$',                            'archweb_dev.wiki.views.main'),

# Feeds
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),

# (mostly) Static Pages
    (r'^$',                'archweb_dev.public.views.index'),
    (r'^about/$',          'archweb_dev.public.views.about'),
    (r'^art/$',            'archweb_dev.public.views.art'),
    (r'^cvs/$',            'archweb_dev.public.views.cvs'),
    (r'^developers/$',     'archweb_dev.public.views.developers'),
    (r'^donate/$',         'archweb_dev.public.views.donate'),
    (r'^download/$',       'archweb_dev.public.views.download'),
    (r'^irc/$',            'archweb_dev.public.views.irc'),
    (r'^moreforums/$',     'archweb_dev.public.views.moreforums'),
    (r'^press/$',          'archweb_dev.public.views.press'),
    (r'^projects/$',       'archweb_dev.public.views.projects'),
    (r'^robots.txt$',      'archweb_dev.public.views.robots'),

# Authentication / Admin
    (r'^denied/$',          'archweb_dev.public.views.denied'),
    (r'^login/$',           'django.contrib.auth.views.login',  {'template_name': 'registration/login.html'}),
    (r'^accounts/login/$',  'django.contrib.auth.views.login',  {'template_name': 'registration/login.html'}),
    (r'^logout/$',          'django.contrib.auth.views.logout', {'template_name': 'registration/logout.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'template_name': 'registration/logout.html'}),
    (r'^admin/',             include('django.contrib.admin.urls')),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', 
            {'document_root': settings.DEPLOY_PATH+'/media'}))

# vim: set ts=4 sw=4 et:

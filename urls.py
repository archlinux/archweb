from django.conf.urls.defaults import *
from archlinux.news.models import News
from archlinux.feeds import PackageFeed, NewsFeed

feeds = {
	'packages': PackageFeed,
	'news':     NewsFeed
}

urlpatterns = patterns('',
	(r'^media/(.*)$',      'django.views.static.serve', {'document_root': '/home/jvinet/shared/work/archlinux/media'}),

# Dynamic Stuff
	(r'^packages/flag/(\d+)/$',          'archlinux.packages.views.flag'),
	(r'^packages/flaghelp/$',            'archlinux.packages.views.flaghelp'),
	(r'^packages/unflag/(\d+)/$',        'archlinux.packages.views.unflag'),
	(r'^packages/files/(\d+)/$',         'archlinux.packages.views.files'),
	(r'^packages/search/$',              'archlinux.packages.views.search'),
	(r'^packages/search/([A-z0-9]+)/$',  'archlinux.packages.views.search'),
	(r'^packages/update/$',              'archlinux.packages.views.update'),
	(r'^packages/(?P<pkgid>\d+)/$',      'archlinux.packages.views.details'),
	(r'^packages/(?P<name>[A-z0-9]+)/$', 'archlinux.packages.views.details'),
	(r'^packages/(?P<repo>[A-z0-9]+)/(?P<name>[A-z0-9]+)/$', 'archlinux.packages.views.details'),
	(r'^packages/$',                     'archlinux.packages.views.search'),

	(r'^todo/(\d+)/$',            'archlinux.todolists.views.view'),
	(r'^todo/add/$',              'archlinux.todolists.views.add'),
	(r'^todo/flag/(\d+)/(\d+)/$', 'archlinux.todolists.views.flag'),
	(r'^todo/$',                  'archlinux.todolists.views.list'),

	(r'^news/(\d+)/$',         'archlinux.news.views.view'),
	(r'^news/add/$',           'archlinux.news.views.add'),
	(r'^news/edit/(\d+)/$',    'archlinux.news.views.edit'),
	(r'^news/delete/(\d+)/$',  'archlinux.news.views.delete'),
	(r'^news/$',               'archlinux.news.views.list'),

	(r'^devel/$',          'archlinux.devel.views.index'),
	(r'^devel/notify/$',   'archlinux.devel.views.change_notify'),
	(r'^devel/profile/$',  'archlinux.devel.views.change_profile'),
	(r'^devel/guide/$',    'archlinux.devel.views.guide'),

	(r'^wiki/([A-Z]+[A-z0-9 :/-]+)/$',      'archlinux.wiki.views.page'),
	(r'^wiki/edit/([A-Z]+[A-z0-9 :/-]+)/$', 'archlinux.wiki.views.edit'),
	(r'^wiki/delete/$',                     'archlinux.wiki.views.delete'),
	(r'^wiki/index/$',                      'archlinux.wiki.views.index'),
	(r'^wiki/$',                            'archlinux.wiki.views.main'),

# Feeds
	(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),

# (mostly) Static Pages
	(r'^$',                'archlinux.public.views.index'),
	(r'^about/$',          'archlinux.public.views.about'),
	(r'^art/$',            'archlinux.public.views.art'),
	(r'^cvs/$',            'archlinux.public.views.cvs'),
	(r'^developers/$',     'archlinux.public.views.developers'),
	(r'^donate/$',         'archlinux.public.views.donate'),
	(r'^download/$',       'archlinux.public.views.download'),
	(r'^irc/$',            'archlinux.public.views.irc'),
	(r'^moreforums/$',     'archlinux.public.views.moreforums'),
	(r'^press/$',          'archlinux.public.views.press'),
	(r'^projects/$',       'archlinux.public.views.projects'),

# Authentication / Admin
	(r'^denied/$',          'archlinux.public.views.denied'),
	(r'^login/$',           'django.contrib.auth.views.login',  {'template_name': 'registration/login.html'}),
	(r'^accounts/login/$',  'django.contrib.auth.views.login',  {'template_name': 'registration/login.html'}),
	(r'^logout/$',          'django.contrib.auth.views.logout', {'template_name': 'registration/logout.html'}),
	(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'template_name': 'registration/logout.html'}),
	(r'^admin/',             include('django.contrib.admin.urls')),
)

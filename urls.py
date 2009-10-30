from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from django.views.generic.create_update import delete_object
from django.contrib.auth.decorators import permission_required

from archweb.main.models import Todolist

admin.autodiscover()

urlpatterns = patterns('',
    (r'^packages/unflag/(\d+)/$',        'archweb.packages.views.unflag'),
    (r'^packages/files/(\d+)/$',         'archweb.packages.views.files'),
    (r'^packages/signoffs/$',              'archweb.packages.views.signoffs'),
    (r'^packages/signoff_package/(?P<arch>[A-z0-9]+)/(?P<pkgname>[A-z0-9\-+.]+)/$',
        'archweb.packages.views.signoff_package'),
    (r'^packages/update/$',              'archweb.packages.views.update'),

    (r'^packages/$',                     'archweb.packages.views.search'),
    (r'^packages/(?P<page>\d+)/$',        'archweb.packages.views.search'),

    (r'^packages/(?P<name>[A-z0-9\-+.]+)/$',
        'archweb.packages.views.details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'archweb.packages.views.details'),
    (r'^packages/(?P<repo>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/$',
        'archweb.packages.views.details'),

    (r'^todo/(\d+)/$',              'archweb.todolists.views.view'),
    (r'^todo/add/$',                'archweb.todolists.views.add'),
    (r'^todo/edit/(?P<list_id>\d+)/$',  'archweb.todolists.views.edit'),
    (r'^todo/flag/(\d+)/(\d+)/$',   'archweb.todolists.views.flag'),
    (r'^todo/delete/(?P<object_id>\d+)/$',
        'archweb.todolists.views.delete_todolist'),
    (r'^todo/$',                    'archweb.todolists.views.list'),

    (r'^news/(\d+)/$',         'archweb.news.views.view'),
    (r'^news/add/$',           'archweb.news.views.add'),
    (r'^news/edit/(\d+)/$',    'archweb.news.views.edit'),
    (r'^news/delete/(\d+)/$',  'archweb.news.views.delete'),
    (r'^news/$',               'archweb.news.views.list'),

    (r'^mirrors/$',        'archweb.devel.views.mirrorlist'),

    (r'^devel/$',          'archweb.devel.views.index'),
    (r'^devel/notify/$',   'archweb.devel.views.change_notify'),
    (r'^devel/profile/$',  'archweb.devel.views.change_profile'),

    (r'^devel/newuser/$', 'archweb.devel.views.new_user_form'),

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
    (r'^$', 'archweb.public.views.index'),
    (r'^about/$', 'archweb.public.views.about'),
    (r'^art/$', 'archweb.public.views.art'),
    (r'^svn/$', 'archweb.public.views.svn'),
    (r'^developers/$', 'archweb.public.views.developers'),
    (r'^fellows/$', 'archweb.public.views.fellows'),
    (r'^donate/$', 'archweb.public.views.donate'),
    (r'^download/$', 'archweb.public.views.download'),
    (r'^irc/$', 'archweb.public.views.irc'),
    (r'^moreforums/$', 'archweb.public.views.moreforums'),
    (r'^projects/$', 'archweb.public.views.projects'),
    ('^jsi18n/$', 'django.views.i18n.null_javascript_catalog',
        {'packages': 'django.conf'}),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', 
            {'document_root': settings.DEPLOY_PATH+'/media'}))

# vim: set ts=4 sw=4 et:


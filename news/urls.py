from django.conf.urls import patterns

urlpatterns = patterns('news.views',
    (r'^$',                         'news_list', {}, 'news-list'),
    (r'^add/$',                     'add'),
    (r'^preview/$',                 'preview'),
    # old news URLs, permanent redirect view so we don't break all links
    (r'^(?P<object_id>\d+)/$',      'view_redirect'),
    (r'^(?P<slug>[-\w]+)/$',        'view'),
    (r'^(?P<slug>[-\w]+)/edit/$',   'edit'),
    (r'^(?P<slug>[-\w]+)/delete/$', 'delete'),
)

# vim: set ts=4 sw=4 et:

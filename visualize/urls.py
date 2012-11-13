from django.conf.urls import patterns

urlpatterns = patterns('visualize.views',
    (r'^$',          'index',     {}, 'visualize-index'),
    (r'^by_arch/$',  'by_arch',   {}, 'visualize-byarch'),
    (r'^by_repo/$',  'by_repo',   {}, 'visualize-byrepo'),
)

# vim: set ts=4 sw=4 et:

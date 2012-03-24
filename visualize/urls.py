from django.conf.urls import patterns

urlpatterns = patterns('visualize.views',
    (r'^$',          'index',     {}, 'visualize-index'),
    (r'^by_arch/$',  'by_arch',   {}, 'visualize-byarch'),
    (r'^by_repo/$',  'by_repo',   {}, 'visualize-byrepo'),
    (r'^pgp_keys/$', 'pgp_keys',  {}, 'visualize-pgp_keys'),
)

# vim: set ts=4 sw=4 et:

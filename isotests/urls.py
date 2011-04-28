from django.conf.urls.defaults import patterns

urlpatterns = patterns('isotests.views',
    (r'^$',     'view_results'),
    (r'^add/$', 'add_result')
)

# vim: set ts=4 sw=4 et:

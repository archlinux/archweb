from django.conf.urls.defaults import patterns

urlpatterns = patterns('isotests.views',
    (r'^$',                                              'view_results'),
    (r'^add/$',                                          'add_result'),
    (r'^thanks/$',                                       'thanks'),
    (r'^results/$',                                      'view_results'),
    (r'^results/(?P<option>[a-z0-9_]+)/(?P<value>.+)/$', 'view_results_for'),
    (r'^results/(?P<isoid>.+)/$',                        'view_results_iso'),
)

# vim: set ts=4 sw=4 et:

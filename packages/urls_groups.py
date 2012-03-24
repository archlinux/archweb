from django.conf.urls import patterns

urlpatterns = patterns('packages.views',
    (r'^$',                     'groups', {}, 'groups-list'),
    (r'^(?P<arch>[A-z0-9]+)/$', 'groups'),
    (r'^(?P<arch>[A-z0-9]+)/(?P<name>[^ /]+)/$', 'group_details'),
)

# vim: set ts=4 sw=4 et:

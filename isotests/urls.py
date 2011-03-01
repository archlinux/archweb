from django.conf.urls.defaults import patterns
from isotests.models import Test

info_dict = {
    'queryset': Test.objects.all()
}

urlpatterns = patterns('isotests.views',
    (r'^add/$', 'add_result')
)

urlpatterns += patterns('',
    (r'^$',     'django.views.generic.list_detail.object_list', info_dict)
)

# vim: set ts=4 sw=4 et:

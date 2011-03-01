from django.conf.urls.defaults import patterns
from isotests.models import Test

info_dict = {
    'queryset': Test.objects.all()
}

urlpatterns = patterns('isotests.views',
                       (r'^$', 'view_results'),
                       (r'^add/$', 'add_result')
                       )

urlpatterns += patterns('',
)

# vim: set ts=4 sw=4 et:

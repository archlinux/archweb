from django.http import Http404
from django.views.decorators.cache import cache_page
from django.views.generic.simple import direct_to_template


RETRO_YEAR_MAP = {
    2002: 'index-20020328.html',
}


@cache_page(1800)
def retro_homepage(request, year):
    year = int(year)
    template = RETRO_YEAR_MAP.get(year, None)
    if template is None:
        raise Http404
    return direct_to_template(request, 'retro/%s' % template, {})

# vim: set ts=4 sw=4 et:

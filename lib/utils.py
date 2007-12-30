from django.core import validators
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render_to_response
from django.template import RequestContext

def validate(errdict, fieldname, fieldval, validator, blankallowed, request):
    """
    A helper function that allows easy access to Django's validators without
    going through a Manipulator object.  Will return a dict of all triggered
    errors.
    """
    if blankallowed and not fieldval:
        return
    alldata = ' '.join(request.POST.values()) + ' '.join(request.GET.values())
    try:
        validator(fieldval, alldata)
    except validators.ValidationError, e:
        if not errdict.has_key(fieldname): 
            errdict[fieldname] = []
        errdict[fieldname].append(e)

def prune_cache(django_page_url):
    if not settings.CACHE:
        return
    cache_prefix = 'views.decorators.cache.cache_page.'
    cache_prefix += settings.CACHE_MIDDLEWARE_KEY_PREFIX + '.'
    cache_postfix = '.d41d8cd98f00b204e9800998ecf8427e'
    cache.delete('%s%s%s' % (cache_prefix,django_page_url,cache_postfix))

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

# vim: set ts=4 sw=4 et:


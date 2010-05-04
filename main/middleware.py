import threading

user_holder = threading.local()
user_holder.user = None

# http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
class AutoUserMiddleware(object):
    '''Saves the current user so it can be retrieved by the admin'''
    def process_request(self, request):
        user_holder.user = request.user


def get_user():
    '''Get the currently logged in request.user'''
    return user_holder.user

# begin copy of stock Django UpdateCacheMiddleware
# this is to address feeds caching issue which makes it horribly
# unperformant

from django.conf import settings
from django.core.cache import cache
from django.utils.cache import get_cache_key, learn_cache_key, patch_response_headers, get_max_age

class UpdateCacheMiddleware(object):
    """
    Response-phase cache middleware that updates the cache if the response is
    cacheable.

    Must be used as part of the two-part update/fetch cache middleware.
    UpdateCacheMiddleware must be the first piece of middleware in
    MIDDLEWARE_CLASSES so that it'll get called last during the response phase.
    """
    def __init__(self):
        self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.cache_anonymous_only = getattr(settings, 'CACHE_MIDDLEWARE_ANONYMOUS_ONLY', False)

    def process_response(self, request, response):
        """Sets the cache, if needed."""
        if not hasattr(request, '_cache_update_cache') or not request._cache_update_cache:
            # We don't need to update the cache, just return.
            return response
        if request.method != 'GET':
            # This is a stronger requirement than above. It is needed
            # because of interactions between this middleware and the
            # HTTPMiddleware, which throws the body of a HEAD-request
            # away before this middleware gets a chance to cache it.
            return response
        if not response.status_code == 200:
            return response
        # Try to get the timeout from the "max-age" section of the "Cache-
        # Control" header before reverting to using the default cache_timeout
        # length.
        timeout = get_max_age(response)
        if timeout == None:
            timeout = self.cache_timeout
        elif timeout == 0:
            # max-age was set to 0, don't bother caching.
            return response
        patch_response_headers(response, timeout)
        if timeout:
            response.content = response.content
            cache_key = learn_cache_key(request, response, timeout, self.key_prefix)
            cache.set(cache_key, response, timeout)
        return response

# vim: set ts=4 sw=4 et:

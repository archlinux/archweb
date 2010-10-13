try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.cache import cache
from django.utils.hashcompat import md5_constructor

CACHE_TIMEOUT = 1800
INVALIDATE_TIMEOUT = 15

CACHE_PACKAGE_KEY = 'cache_package_latest'
CACHE_NEWS_KEY = 'cache_news_latest'

def cache_function_key(func, args, kwargs):
    raw = [func.__name__, func.__module__, args, kwargs]
    pickled = pickle.dumps(raw, protocol=pickle.HIGHEST_PROTOCOL)
    key = md5_constructor(pickled).hexdigest()
    return 'cache_function.' + func.__name__ + '.' + key

def cache_function(length):
    """
    A variant of the snippet posted by Jeff Wheeler at
    http://www.djangosnippets.org/snippets/109/

    Caches a function, using the function and its arguments as the key, and the
    return value as the value saved. It passes all arguments on to the
    function, as it should.

    The decorator itself takes a length argument, which is the number of
    seconds the cache will keep the result around.
    """
    def decorator(func):
        def inner_func(*args, **kwargs):
            key = cache_function_key(func, args, kwargs)
            value = cache.get(key)
            if value is not None:
                return value
            else:
                result = func(*args, **kwargs)
                cache.set(key, result, length)
                return result
        return inner_func
    return decorator

def clear_cache_function(func, args, kwargs):
    key = cache_function_key(func, args, kwargs)
    cache.delete(key)

# utility to make a pair of django choices
make_choice = lambda l: [(str(m), str(m)) for m in l]

# These are in here because we would be jumping around in some import circles
# and hoops otherwise. The only thing currently using these keys is the feed
# caching stuff.

def refresh_package_latest(**kwargs):
    # We could delete the value, but that could open a race condition
    # where the new data wouldn't have been committed yet by the calling
    # thread. Instead, explicitly set it to None for a short amount of time.
    # Hopefully by the time it expires we will have committed, and the cache
    # will be valid again. See "Scaling Django" by Mike Malone, slide 30.
    cache.set(CACHE_PACKAGE_KEY, None, INVALIDATE_TIMEOUT)

def refresh_news_latest(**kwargs):
    # same thoughts apply as in refresh_package_latest
    cache.set(CACHE_NEWS_KEY, None, INVALIDATE_TIMEOUT)

# vim: set ts=4 sw=4 et:

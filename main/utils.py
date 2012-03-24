try:
    import cPickle as pickle
except ImportError:
    import pickle

from datetime import datetime
import hashlib
from pytz import utc

from django.core.cache import cache


CACHE_TIMEOUT = 1800
INVALIDATE_TIMEOUT = 10
CACHE_LATEST_PREFIX = 'cache_latest_'


def cache_function_key(func, args, kwargs):
    raw = [func.__name__, func.__module__, args, kwargs]
    pickled = pickle.dumps(raw, protocol=pickle.HIGHEST_PROTOCOL)
    key = hashlib.md5(pickled).hexdigest()
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

def refresh_latest(**kwargs):
    '''A post_save signal handler to clear out the cached latest value for a
    given model.'''
    cache_key = CACHE_LATEST_PREFIX + kwargs['sender'].__name__
    # We could delete the value, but that could open a race condition
    # where the new data wouldn't have been committed yet by the calling
    # thread. Instead, explicitly set it to None for a short amount of time.
    # Hopefully by the time it expires we will have committed, and the cache
    # will be valid again. See "Scaling Django" by Mike Malone, slide 30.
    cache.set(cache_key, None, INVALIDATE_TIMEOUT)


def retrieve_latest(sender):
    # we could break this down based on the request url, but it would probably
    # cost us more in query time to do so.
    cache_key = CACHE_LATEST_PREFIX + sender.__name__
    latest = cache.get(cache_key)
    if latest:
        return latest
    try:
        latest_by = sender._meta.get_latest_by
        latest = sender.objects.values(latest_by).latest()[latest_by]
        # Using add means "don't overwrite anything in there". What could be in
        # there is an explicit None value that our refresh signal set, which
        # means we want to avoid race condition possibilities for a bit.
        cache.add(cache_key, latest, CACHE_TIMEOUT)
        return latest
    except sender.DoesNotExist:
        pass
    return None


def utc_now():
    '''Returns a timezone-aware UTC date representing now.'''
    return datetime.utcnow().replace(tzinfo=utc)


def set_created_field(sender, **kwargs):
    '''This will set the 'created' field on any object to the current UTC time
    if it is unset. For use as a pre_save signal handler.'''
    obj = kwargs['instance']
    if hasattr(obj, 'created') and not obj.created:
        obj.created = utc_now()


def groupby_preserve_order(iterable, keyfunc):
    '''Take an iterable and regroup using keyfunc to determine whether items
    belong to the same group. The order of the iterable is preserved and
    similar keys do not have to be consecutive. This means the earliest
    occurrence of a given key will determine the order of the lists in the
    returned list.'''
    seen_keys = {}
    result = []
    for item in iterable:
        key = keyfunc(item)

        group = seen_keys.get(key, None)
        if group is None:
            group = []
            seen_keys[key] = group
            result.append(group)

        group.append(item)

    return result


class PackageStandin(object):
    '''Resembles a Package object, and has a few of the same fields, but is
    really a link to a pkgbase that has no package with matching pkgname.'''
    def __init__(self, package):
        self.package = package
        self.pkgname = package.pkgbase

    def __getattr__(self, name):
        return getattr(self.package, name)

    def get_absolute_url(self):
        return '/packages/%s/%s/%s/' % (
                self.repo.name.lower(), self.arch.name, self.pkgbase)

# vim: set ts=4 sw=4 et:

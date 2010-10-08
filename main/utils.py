try:
    import cPickle as pickle
except ImportError:
    import pickle
from django.core.cache import cache
from django.utils.hashcompat import md5_constructor

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
            raw = [func.__name__, func.__module__, args, kwargs]
            pickled = pickle.dumps(raw, protocol=pickle.HIGHEST_PROTOCOL)
            key = md5_constructor(pickled).hexdigest()
            key = 'cache_function.' + func.__name__ + '.' + key
            value = cache.get(key)
            if value is not None:
                return value
            else:
                result = func(*args, **kwargs)
                cache.set(key, result, length)
                return result
        return inner_func
    return decorator

#utility to make a pair of django choices
make_choice = lambda l: [(str(m), str(m)) for m in l]

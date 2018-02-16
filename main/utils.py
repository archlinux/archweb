try:
    import pickle as pickle
except ImportError:
    import pickle

import hashlib
import markdown
from markdown.extensions import Extension

from django.core.cache import cache
from django.db import connections, router
from django.http import HttpResponse
from django.utils.timezone import now
from django.template.defaultfilters import slugify


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


def empty_response():
    empty = HttpResponse('')
    # designating response as 'streaming' forces ConditionalGetMiddleware to
    # not add a 'Content-Length: 0' header
    empty.streaming = True
    return empty


def format_http_headers(request):
    headers = sorted((k, v) for k, v in list(request.META.items())
            if k.startswith('HTTP_'))
    data = []
    for k, v in headers:
        data.extend([k[5:].replace('_', '-').title(), ': ', v, '\n'])
    return ''.join(data)


# utility to make a pair of django choices
make_choice = lambda l: [(str(m), str(m)) for m in l]


def set_created_field(sender, **kwargs):
    '''This will set the 'created' field on any object to the current UTC time
    if it is unset.
    Additionally, this will set the 'last_modified' field on any object to the
    current UTC time on any save of the object.
    For use as a pre_save signal handler.'''
    obj = kwargs['instance']
    time = now()
    if hasattr(obj, 'created') and not obj.created:
        obj.created = time
    if hasattr(obj, 'last_modified'):
        obj.last_modified = time


def find_unique_slug(model, title):
    '''Attempt to find a unique slug for this model with given title.'''
    existing = set(model.objects.values_list(
        'slug', flat=True).order_by().distinct())

    suffixed = slug = slugify(title)
    suffix = 0
    while suffixed in existing:
        suffix += 1
        suffixed = "%s-%d" % (slug, suffix)

    return suffixed


def database_vendor(model, mode='read'):
    if mode == 'read':
        database = router.db_for_read(model)
    elif mode == 'write':
        database = router.db_for_write(model)
    else:
        raise Exception('Invalid database mode specified')
    return connections[database].vendor


class EscapeHtml(Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['html_block']
        del md.inlinePatterns['html']


def parse_markdown(text, allow_html=False):
    if allow_html:
        return markdown.markdown(text, enable_attributes=False)
    ext = [EscapeHtml()]
    return markdown.markdown(text, extensions=ext, enable_attributes=False)


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


class DependStandin(object):
    '''Resembles a Depend object, and has a few of the same fields, but is
    really a link to a base package rather than a single package.'''
    def __init__(self, depends):
        self._depends = depends
        first = depends[0]
        self.name = first.name
        self.version = first.version
        self.comparison = first.comparison
        self.description = first.description
        self.deptype = first.deptype
        self.pkg = first.pkg.base_package() or PackageStandin(first.pkg)

# vim: set ts=4 sw=4 et:

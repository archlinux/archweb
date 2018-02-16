# Derived from Django snippets: http://djangosnippets.org/snippets/2242/
from collections import OrderedDict
from datetime import datetime, timedelta
from hashlib import md5
import traceback
from pytz import utc


class LimitedSizeDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.size_limit = kwargs.pop('size', None)
        if self.size_limit == 0:
            self.size_limit = None
        if self.size_limit and self.size_limit < 0:
            raise Exception('Invalid size specified')
        super(LimitedSizeDict, self).__init__(*args, **kwargs)
        self.check_item_limits()

    def __setitem__(self, key, value):
        # delete and add to ensure it ends up at the end of the linked list
        if key in self:
            super(LimitedSizeDict, self).__delitem__(key)
        super(LimitedSizeDict, self).__setitem__(key, value)
        self.check_item_limits()

    def check_item_limits(self):
        if self.size_limit is None:
            return
        while len(self) > self.size_limit:
            self.popitem(last=False)


class RateLimitFilter(object):
    def __init__(self, name='', rate=10, prefix='error_rate', max_keys=100):
        # delayed import otherwise we have a circular dep when setting up
        # the logging config: settings -> logging -> cache -> settings
        self.cache_module = __import__('django.core.cache', fromlist=['cache'])
        self.errors = LimitedSizeDict(size=max_keys)
        self.rate = rate
        self.prefix = prefix

    def filter(self, record):
        if self.rate == 0:
            # rate == 0 means totally unfiltered
            return True

        trace = '\n'.join(traceback.format_exception(*record.exc_info))
        key = md5(trace.encode('utf-8')).hexdigest()
        cache = self.cache_module.cache

        # Test if the cache works
        try:
            cache.set(self.prefix, 1, 300)
            use_cache = (cache.get(self.prefix) == 1)
        except:
            use_cache = False

        if use_cache:
            cache_key = '%s_%s' % (self.prefix, key)
            duplicate = (cache.get(cache_key) == 1)
            cache.set(cache_key, 1, self.rate)
        else:
            now = datetime.utcnow().replace(tzinfo=utc)
            min_date = now - timedelta(seconds=self.rate)
            duplicate = (key in self.errors and self.errors[key] >= min_date)
            self.errors[key] = now

        return not duplicate

# vim: set ts=4 sw=4 et:

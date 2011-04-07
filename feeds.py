import datetime
from decimal import Decimal, ROUND_HALF_DOWN

from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.db.models import Q
from django.utils.hashcompat import md5_constructor
from django.views.decorators.http import condition

from main.models import Arch, Repo, Package
from main.utils import CACHE_TIMEOUT, INVALIDATE_TIMEOUT
from main.utils import CACHE_PACKAGE_KEY, CACHE_NEWS_KEY
from news.models import News

def utc_offset():
    '''Calculate the UTC offset from local time. Useful for converting values
    stored in local time to things like cache last modifed headers.'''
    timediff = datetime.datetime.utcnow() - datetime.datetime.now()
    secs = timediff.days * 86400 + timediff.seconds
    # round to nearest minute
    mins = Decimal(secs) / Decimal(60)
    mins = mins.quantize(Decimal('0'), rounding=ROUND_HALF_DOWN)
    return datetime.timedelta(minutes=int(mins))


def retrieve_package_latest():
    # we could break this down based on the request url, but it would probably
    # cost us more in query time to do so.
    latest = cache.get(CACHE_PACKAGE_KEY)
    if latest:
        return latest
    try:
        latest = Package.objects.values('last_update').latest(
                'last_update')['last_update']
        latest = latest + utc_offset()
        # Using add means "don't overwrite anything in there". What could be in
        # there is an explicit None value that our refresh signal set, which
        # means we want to avoid race condition possibilities for a bit.
        cache.add(CACHE_PACKAGE_KEY, latest, CACHE_TIMEOUT)
        return latest
    except Package.DoesNotExist:
        pass
    return None

def package_etag(request, *args, **kwargs):
    latest = retrieve_package_latest()
    if latest:
        return md5_constructor(str(kwargs) + str(latest)).hexdigest()
    return None

def package_last_modified(request, *args, **kwargs):
    return retrieve_package_latest()

class PackageFeed(Feed):
    link = '/packages/'
    title_template = 'feeds/packages_title.html'
    description_template = 'feeds/packages_description.html'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(etag_func=package_etag, last_modified_func=package_last_modified)
        return wrapper(super(PackageFeed, self).__call__)(request, *args, **kwargs)

    def get_object(self, request, arch='', repo=''):
        obj = dict()
        qs = Package.objects.select_related('arch', 'repo').order_by(
                '-last_update')

        if arch != '':
            # feed for a single arch, also include 'any' packages everywhere
            a = Arch.objects.get(name=arch)
            qs = qs.filter(Q(arch=a) | Q(arch__agnostic=True))
            obj['arch'] = a
        if repo != '':
            # feed for a single arch AND repo
            r = Repo.objects.get(name__iexact=repo)
            qs = qs.filter(repo=r)
            obj['repo'] = r
        obj['qs'] = qs[:50]
        return obj

    def title(self, obj):
        s = 'Arch Linux: Recent package updates'
        if 'repo' in obj:
            s += ' (%s [%s])' % (obj['arch'].name, obj['repo'].name.lower())
        elif 'arch' in obj:
            s += ' (%s)' % (obj['arch'].name)
        return s

    def description(self, obj):
        s = 'Recently updated packages in the Arch Linux package repositories'
        if 'arch' in obj:
            s += ' for the \'%s\' architecture' % obj['arch'].name.lower()
            if not obj['arch'].agnostic:
                s += ' (including \'any\' packages)'
        if 'repo' in obj:
            s += ' in the [%s] repository' % obj['repo'].name.lower()
        s += '.'
        return s

    subtitle = description

    def items(self, obj):
        return obj['qs']

    def item_guid(self, item):
        # http://diveintomark.org/archives/2004/05/28/howto-atom-id
        date = item.last_update
        return 'tag:%s,%s:%s%s' % (Site.objects.get_current().domain,
                date.strftime('%Y-%m-%d'), item.get_absolute_url(),
                date.strftime('%Y%m%d%H%M'))

    def item_pubdate(self, item):
        return item.last_update

    def item_categories(self, item):
        return (item.repo.name, item.arch.name)


def retrieve_news_latest():
    latest = cache.get(CACHE_NEWS_KEY)
    if latest:
        return latest
    try:
        latest = News.objects.values('last_modified').latest(
                'last_modified')['last_modified']
        latest = latest + utc_offset()
        # same thoughts apply as in retrieve_package_latest
        cache.add(CACHE_NEWS_KEY, latest, CACHE_TIMEOUT)
        return latest
    except News.DoesNotExist:
        pass
    return None

def news_etag(request, *args, **kwargs):
    latest = retrieve_news_latest()
    if latest:
        return md5_constructor(str(latest)).hexdigest()
    return None

def news_last_modified(request, *args, **kwargs):
    return retrieve_news_latest()

class NewsFeed(Feed):
    title = 'Arch Linux: Recent news updates'
    link = '/news/'
    description = 'The latest and greatest news from the Arch Linux distribution.'
    subtitle = description
    title_template = 'feeds/news_title.html'
    description_template = 'feeds/news_description.html'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(etag_func=news_etag, last_modified_func=news_last_modified)
        return wrapper(super(NewsFeed, self).__call__)(request, *args, **kwargs)

    def items(self):
        return News.objects.select_related('author').order_by(
                '-postdate', '-id')[:10]

    def item_guid(self, item):
        return item.guid

    def item_pubdate(self, item):
        return item.postdate

    def item_author_name(self, item):
        return item.author.get_full_name()

# vim: set ts=4 sw=4 et:

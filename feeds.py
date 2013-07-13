from datetime import datetime, time
import hashlib
from pytz import utc

from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.decorators.http import condition

from main.utils import retrieve_latest
from main.models import Arch, Repo, Package
from news.models import News
from releng.models import Release


class GuidNotPermalinkFeed(Rss201rev2Feed):
    @staticmethod
    def check_for_unique_id(f):
        def wrapper(name, contents=None, attrs=None):
            if attrs is None:
                attrs = {}
            if name == 'guid':
                attrs['isPermaLink'] = 'false'
            return f(name, contents, attrs)
        return wrapper

    def write_items(self, handler):
        # Totally disgusting. Monkey-patch the hander so if it sees a
        # 'unique-id' field come through, add an isPermalink="false" attribute.
        # Workaround for http://code.djangoproject.com/ticket/9800
        handler.addQuickElement = self.check_for_unique_id(
                handler.addQuickElement)
        super(GuidNotPermalinkFeed, self).write_items(handler)


def package_etag(request, *args, **kwargs):
    latest = retrieve_latest(Package)
    if latest:
        return hashlib.md5(str(kwargs) + str(latest)).hexdigest()
    return None

def package_last_modified(request, *args, **kwargs):
    return retrieve_latest(Package)


class PackageFeed(Feed):
    feed_type = GuidNotPermalinkFeed

    link = '/packages/'
    title_template = 'feeds/packages_title.html'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(etag_func=package_etag, last_modified_func=package_last_modified)
        return wrapper(super(PackageFeed, self).__call__)(request, *args, **kwargs)

    __name__ = 'package_feed'

    def get_object(self, request, arch='', repo=''):
        obj = dict()
        qs = Package.objects.normal().order_by('-last_update')

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
        else:
            qs = qs.filter(repo__staging=False)
        obj['qs'] = qs[:50]
        return obj

    def title(self, obj):
        s = 'Arch Linux: Recent package updates'
        if 'repo' in obj and 'arch' in obj:
            s += ' (%s [%s])' % (obj['arch'].name, obj['repo'].name.lower())
        elif 'repo' in obj:
            s += ' [%s]' % (obj['repo'].name.lower())
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

    def item_description(self, item):
        return item.pkgdesc

    def item_categories(self, item):
        return (item.repo.name, item.arch.name)


def news_etag(request, *args, **kwargs):
    latest = retrieve_latest(News, 'last_modified')
    if latest:
        return hashlib.md5(str(latest)).hexdigest()
    return None

def news_last_modified(request, *args, **kwargs):
    return retrieve_latest(News, 'last_modified')


class NewsFeed(Feed):
    feed_type = GuidNotPermalinkFeed

    title = 'Arch Linux: Recent news updates'
    link = '/news/'
    description = 'The latest and greatest news from the Arch Linux distribution.'
    subtitle = description
    description_template = 'feeds/news_description.html'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(etag_func=news_etag, last_modified_func=news_last_modified)
        return wrapper(super(NewsFeed, self).__call__)(request, *args, **kwargs)

    __name__ = 'news_feed'

    def items(self):
        return News.objects.select_related('author').order_by(
                '-postdate', '-id')[:10]

    def item_guid(self, item):
        return item.guid

    def item_pubdate(self, item):
        return item.postdate

    def item_author_name(self, item):
        return item.author.get_full_name()

    def item_title(self, item):
        return item.title


class ReleaseFeed(Feed):
    feed_type = GuidNotPermalinkFeed

    title = 'Arch Linux: Releases'
    link = '/download/'
    description = 'Release ISOs'
    subtitle = description

    __name__ = 'release_feed'

    def items(self):
        return Release.objects.filter(available=True)[:10]

    def item_title(self, item):
        return item.version

    def item_description(self, item):
        return item.info_html()

    def item_pubdate(self, item):
        return datetime.combine(item.release_date, time()).replace(tzinfo=utc)

    def item_guid(self, item):
        # http://diveintomark.org/archives/2004/05/28/howto-atom-id
        date = item.release_date
        return 'tag:%s,%s:%s' % (Site.objects.get_current().domain,
                date.strftime('%Y-%m-%d'), item.get_absolute_url())

    def item_enclosure_url(self, item):
        domain = Site.objects.get_current().domain
        proto = 'https'
        return "%s://%s/%s.torrent" % (proto, domain, item.iso_url())

    def item_enclosure_length(self, item):
        return item.file_size or ""

    item_enclosure_mime_type = 'application/x-bittorrent'

# vim: set ts=4 sw=4 et:

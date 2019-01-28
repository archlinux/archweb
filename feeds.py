from datetime import datetime, time
from pytz import utc

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.models import ADDITION, DELETION
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.db import connection
from django.db.models import Q
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.decorators.http import condition

from main.models import Arch, Repo, Package
from news.models import News
from packages.models import Update
from releng.models import Release


class BatchWritesWrapper(object):
    def __init__(self, outfile):
        self.outfile = outfile
        self.buf = []

    def write(self, s):
        buf = self.buf
        buf.append(s)
        if len(buf) >= 40:
            self.outfile.write(b''.join(buf))
            self.buf = []

    def flush(self):
        self.outfile.write(b''.join(self.buf))
        self.outfile.flush()


class FasterRssFeed(Rss201rev2Feed):
    def write(self, outfile, encoding):
        '''
        Batch the underlying 'write' calls on the outfile because Python's
        default saxutils XmlGenerator is a POS that insists on unbuffered
        write/flush calls. This sucks when it is making 1-byte calls to write
        '>' closing tags and over 1600 write calls in our package feed.
        '''
        wrapper = BatchWritesWrapper(outfile)
        super(FasterRssFeed, self).write(wrapper, encoding)
        wrapper.flush()


def package_last_modified(request, *args, **kwargs):
    try:
        return Package.objects.latest('last_update').last_update
    except ObjectDoesNotExist:
        return


class PackageFeed(Feed):
    feed_type = FasterRssFeed

    link = '/packages/'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(last_modified_func=package_last_modified)
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

    item_guid_is_permalink = False

    def item_guid(self, item):
        # http://diveintomark.org/archives/2004/05/28/howto-atom-id
        date = item.last_update
        return 'tag:%s,%s:%s%s' % (Site.objects.get_current().domain,
                date.strftime('%Y-%m-%d'), item.get_absolute_url(),
                date.strftime('%Y%m%d%H%M'))

    def item_pubdate(self, item):
        return item.last_update

    def item_title(self, item):
        return '%s %s %s' % (item.pkgname, item.full_version, item.arch.name)

    def item_description(self, item):
        return item.pkgdesc

    def item_categories(self, item):
        return (item.repo.name, item.arch.name)

def removal_last_modified(request, *args, **kwargs):
    try:
        return Update.objects.latest('created').created
    except ObjectDoesNotExist:
        return


class PackageUpdatesFeed(Feed):
    feed_type = FasterRssFeed
    link = '/packages/'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(last_modified_func=removal_last_modified)
        return wrapper(super(PackageUpdatesFeed, self).__call__)(request, *args, **kwargs)

    __name__ = 'packages_updates_feed'

    def get_object(self, request, operation='', arch='', repo=''):
        obj = dict()

        if 'added' in request.path:
            flag = ADDITION
            obj['action'] = 'added'
        elif 'removed' in request.path:
            flag = DELETION
            obj['action'] = 'removed'

        qs = Update.objects.filter(action_flag=flag).order_by('-created')

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
        s = 'Arch Linux: Recent {} packages'.format(obj['action'])
        if 'repo' in obj and 'arch' in obj:
            s += ' (%s [%s])' % (obj['arch'].name, obj['repo'].name.lower())
        elif 'repo' in obj:
            s += ' [%s]' % (obj['repo'].name.lower())
        elif 'arch' in obj:
            s += ' (%s)' % (obj['arch'].name)
        return s

    def description(self, obj):
        s = 'Recently {} packages in the Arch Linux package repositories'.format(obj['action'])
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

    item_guid_is_permalink = False

    def item_guid(self, item):
        # http://diveintomark.org/archives/2004/05/28/howto-atom-id
        date = item.created
        return 'tag:%s,%s:%s%s' % (Site.objects.get_current().domain,
                date.strftime('%Y-%m-%d'), item.get_absolute_url(),
                date.strftime('%Y%m%d%H%M'))

    def item_pubdate(self, item):
        return item.created

    def item_title(self, item):
        return '%s %s' % (item.pkgname, item.arch.name)

    def item_description(self, item):
        return item.pkgname

    def item_categories(self, item):
        return (item.repo.name, item.arch.name)


def news_last_modified(request, *args, **kwargs):
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(last_modified) FROM news")
    return cursor.fetchone()[0]


class NewsFeed(Feed):
    feed_type = FasterRssFeed

    title = 'Arch Linux: Recent news updates'
    link = '/news/'
    description = 'The latest and greatest news from the Arch Linux distribution.'
    subtitle = description

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(last_modified_func=news_last_modified)
        return wrapper(super(NewsFeed, self).__call__)(request, *args, **kwargs)

    __name__ = 'news_feed'

    def items(self):
        return News.objects.select_related('author').order_by(
                '-postdate', '-id')[:10]

    item_guid_is_permalink = False

    def item_guid(self, item):
        return item.guid

    def item_pubdate(self, item):
        return item.postdate

    def item_updateddate(self, item):
        return item.last_modified

    def item_author_name(self, item):
        return item.author.get_full_name()

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.html()


class ReleaseFeed(Feed):
    feed_type = FasterRssFeed

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

    def item_updateddate(self, item):
        return item.last_modified

    item_guid_is_permalink = False

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
        if item.torrent_data:
            torrent = item.torrent()
            return torrent['file_length'] or ""
        return ""

    item_enclosure_mime_type = 'application/x-bittorrent'

# vim: set ts=4 sw=4 et:

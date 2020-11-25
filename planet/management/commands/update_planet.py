"""
update_planet

Imports all feeds for users who have filled in a valid website and website_rss,
the amount of items imported is limited to the defined FEED_LIMT

Usage: ./manage.py update_planet
"""


import logging
import sys
import time

from datetime import datetime
from pytz import utc

import bleach
import feedparser

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.template.defaultfilters import truncatewords_html
from django.conf import settings

from planet.models import Feed, FeedItem, FEEDITEM_SUMMARY_LIMIT


logging.basicConfig(
    level=logging.WARNING,
    format=u'%(asctime)s -> %(levelname)s: %(message)s',
    datefmt=u'%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class ItemOlderThenLatest(Exception):
    pass


class Command(BaseCommand):

    def parse_feed(self, feed_instance):
        latest = None
        items = []
        url = feed_instance.website_rss

        logger.debug("Import new feed items for '%s'", url)

        try:
            latest = FeedItem.objects.filter(feed=feed_instance).latest()
        except FeedItem.DoesNotExist:
            pass

        etag = cache.get(f'planet:etag:{url}')
        feed = feedparser.parse(url, etag=etag)
        http_status = feed.get('status')

        if not http_status:
            logger.info("The feed '%s' returns no HTTP status", url)

        if http_status == 304:
            logger.info("The feed '%s' has not changed since we last checked it", url)
            if 'etag' in feed:
                cache.set(f'planet:etag:{url}', feed.etag, 86400)
            return

        if http_status == 301:
            logging.info("The feed '%s' has moved permanently to '%s'", url, feed.href)
            feed_instance.website_rss = feed.href
            feed_instance.save()
            return

        if http_status != 200:
            logger.info("error parsing feed: '%s', status: '%s'", url, http_status)
            return

        if not feed.entries:
            logger.info("error parsing feed: '%s', feed has no more new entries", url)
            return

        for entry in feed.entries[:settings.RSS_FEED_LIMIT]:
            try:
                item = self.parse_entry(entry, feed_instance, latest)
            except ItemOlderThenLatest:
                break

            if not item:
                continue

            items.append(item)

        logger.debug("inserting %d feed entries", len(items))
        res = FeedItem.objects.bulk_create(items)

        if res and 'etag' in feed:
            # Cache etag for one day
            logger.debug("cache etag for '%s'", url)
            cache.set(f'planet:etag:{url}', feed.etag, 86400)

    def parse_entry(self, entry, feed_instance, latest):
        url = feed_instance.website_rss
        published_parsed = entry.get('published_parsed')
        # Maybe it's an atom feed?
        if not published_parsed:
            published_parsed = entry.get('updated_parsed')

        if not published_parsed:
            logger.error("feed: '%s' has no published or updated date", url)
            return

        published = datetime.fromtimestamp(time.mktime(published_parsed)).replace(tzinfo=utc)

        if latest and latest.publishdate >= published:
            logger.debug("feed: '%s' has no more new entries", url)
            raise ItemOlderThenLatest()

        if not entry.link:
            logger.error("feed '%s' entry has no link, skipping", url)
            return

        logger.debug("import feed entry '%s'", entry.title)

        item = FeedItem(title=entry.title, publishdate=published, url=entry.link)
        item.feed = feed_instance

        if entry.get('description'):
            summary = bleach.clean(entry.description, strip=True)
            if len(summary) > FEEDITEM_SUMMARY_LIMIT:
                summary = truncatewords_html(summary, 100)
            item.summary = summary

        if entry.get('author'):
            item.author = entry.get('author')

        return item

    def handle(self, *args, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        for feed in Feed.objects.all():
            self.parse_feed(feed)

            # Only keep RSS_FEED_LIMIT amount of feed items.
            feeds_to_keep = FeedItem.objects.filter(feed=feed).order_by('-publishdate')[:settings.RSS_FEED_LIMIT]
            items = FeedItem.objects.filter(feed=feed).exclude(pk__in=feeds_to_keep).delete()
            logger.debug("removed %d feed entries", items[0])

# vim: set ts=4 sw=4 et:

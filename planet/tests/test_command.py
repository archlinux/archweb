import time
from unittest import mock

from django.test import TestCase

from planet.models import Feed, FeedItem
from planet.management.commands.update_planet import Command


class Result(dict):
    status = 200
    entries = []

    def get(self, value):
        return getattr(self, value)


class Entry(dict):
    title = 'title'
    description = 'lorem ipsum'
    author = 'John Doe'
    published_parsed = time.localtime(time.time())
    link = 'https://archlinux.org'
    updated_parsed = None

    def get(self, value):
        return getattr(self, value)


class UpdatePlanetTest(TestCase):

    def setUp(self):
        self.command = Command()
        self.feed = Feed(title='test', website='http://archlinux.org',
                         website_rss='http://archlinux.org/feed.rss')

    # Test when feedparser receives an exception and returns no status
    @mock.patch('feedparser.parse')
    def test_parse_feed_wrong(self, parse):
        parse.return_value = {}
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 0

    @mock.patch('feedparser.parse')
    def test_parse_feed_304(self, parse):
        parse.return_value = {'status': 304}
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 0

    @mock.patch('feedparser.parse')
    def test_parse_feed_unknown(self, parse):
        parse.return_value = {'status': 201}
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 0

    @mock.patch('feedparser.parse')
    def test_parse_entries_empty(self, parse):
        parse.return_value = Result()
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 0

    @mock.patch('feedparser.parse')
    def test_parse_entries_not_published(self, parse):
        value = Result()
        entry = Entry()
        entry.published_parsed = None
        value.entries = [entry]
        parse.return_value = value
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 0

    @mock.patch('feedparser.parse')
    def test_parse_entries(self, parse):
        value = Result()
        value.entries = [Entry()]
        parse.return_value = value
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 1

    @mock.patch('feedparser.parse')
    def test_parse_entries_atom(self, parse):
        value = Result()
        entry = Entry()
        entry.published_parsed = None
        entry.updated_parsed = time.localtime(time.time())

        value.entries = [entry]
        parse.return_value = value
        self.command.parse_feed(self.feed)
        assert FeedItem.objects.count() == 1

    @mock.patch('feedparser.parse')
    def test_parse_feed_301(self, parse):
        return_value = Result()
        return_value.status = 301
        return_value.href = 'https://example.com/rss'
        parse.return_value = return_value
        self.command.parse_feed(self.feed)
        assert self.feed.website_rss == return_value.href

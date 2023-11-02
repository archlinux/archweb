import time
from unittest import mock

import feedparser
import pytest

from planet.management.commands.update_planet import Command
from planet.models import FEEDITEM_SUMMARY_LIMIT, Feed, FeedItem


@pytest.fixture
def command():
    yield Command()


@pytest.fixture
def feed(db):
    return Feed(title='test', website='http://archlinux.org',
                website_rss='http://archlinux.org/feed.rss')


class MockParse:
    @staticmethod
    def parse():
        return {}


@pytest.fixture
def mock_parse(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockParse()
    monkeypatch.setattr(feedparser, "parse", mock_get)


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


# Test when feedparser receives an exception and returns no status
def test_parse_feed_wrong(feed, command):
    with mock.patch('feedparser.parse') as parse:
        parse.return_value = {}
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 0


def test_parse_feed_304(feed, command):
    with mock.patch('feedparser.parse') as parse:
        parse.return_value = {'status': 304}
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 0


def test_parse_feed_unknown(feed, command):
    with mock.patch('feedparser.parse') as parse:
        parse.return_value = {'status': 201}
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 0


def test_parse_entries_empty(feed, command):
    with mock.patch('feedparser.parse') as parse:
        parse.return_value = Result()
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 0


def test_parse_entries_not_published(feed, command):
    with mock.patch('feedparser.parse') as parse:
        feed.save()
        value = Result()
        entry = Entry()
        entry.published_parsed = None
        value.entries = [entry]
        parse.return_value = value
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 0


def test_parse_entries(feed, command):
    with mock.patch('feedparser.parse') as parse:
        feed.save()
        value = Result()
        value.entries = [Entry()]
        parse.return_value = value
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 1


def test_parse_no_new_entries(feed, command):
    with mock.patch('feedparser.parse') as parse:
        feed.save()
        value = Result()
        value.entries = [Entry()]
        parse.return_value = value
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 1
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 1


def test_parse_no_link(feed, command):
    with mock.patch('feedparser.parse') as parse:
        feed.save()
        value = Result()
        entry = Entry()
        entry.link = ''
        value.entries = [entry]
        parse.return_value = value
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 0


def test_parse_entries_atom(feed, command):
    with mock.patch('feedparser.parse') as parse:
        feed.save()
        value = Result()
        entry = Entry()
        entry.published_parsed = None
        entry.updated_parsed = time.localtime(time.time())

        value.entries = [entry]
        parse.return_value = value
        command.parse_feed(feed)
        assert FeedItem.objects.count() == 1


def test_parse_feed_301(feed, command):
    with mock.patch('feedparser.parse') as parse:
        return_value = Result()
        return_value.status = 301
        return_value.href = 'https://example.com/rss'
        parse.return_value = return_value
        command.parse_feed(feed)
        assert feed.website_rss == return_value.href


def test_parse_item_summary(feed, command):
    with mock.patch('feedparser.parse') as parse:
        feed.save()
        value = Result()
        entry = Entry()
        entry.description = ' '.join(['x' * 4 for x in range(0, FEEDITEM_SUMMARY_LIMIT * 4, 4)])

        value.entries = [entry]
        parse.return_value = value
        command.parse_feed(feed)
        feed = FeedItem.objects.first()
        assert len(feed.summary) < FEEDITEM_SUMMARY_LIMIT

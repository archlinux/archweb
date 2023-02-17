from datetime import datetime, timezone

import feedparser

from planet.models import FeedItem


def test_feed(db, client):
    response = client.get('/feeds/planet/')
    assert response.status_code == 200
    feed = feedparser.parse(response.content)
    assert feed['feed']['title'] == 'Planet Arch Linux'


def test_feed_item(db, client):
    publishdate = datetime.now(timezone.utc)
    FeedItem.objects.create(publishdate=publishdate, title='A title', summary='A summary', author='John Doe')

    response = client.get('/feeds/planet/')

    feed_entry = feedparser.parse(response.content)['entries'][0]
    assert feed_entry['published'] == publishdate.strftime('%a, %d %b %Y 00:00:00 +0000')
    assert feed_entry['title'] == 'A title'
    assert feed_entry['summary'] == 'A summary'
    assert feed_entry['author'] == 'John Doe'


def test_planet(db, client):
    response = client.get('/planet/')
    assert response.status_code == 200

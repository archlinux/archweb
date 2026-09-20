from datetime import datetime, timezone

import feedparser
import pytest
from django.test import Client

from planet.models import FeedItem


@pytest.mark.django_db
def test_feed(client: Client) -> None:
    response = client.get('/feeds/planet/')
    assert response.status_code == 200
    feed = feedparser.parse(response.content)
    assert feed['feed']['title'] == 'Planet Arch Linux'


@pytest.mark.django_db
def test_feed_item(client):
    publishdate = datetime.now(timezone.utc)
    FeedItem.objects.create(publishdate=publishdate, title='A title', summary='A summary', author='John Doe')

    response = client.get('/feeds/planet/')

    feed_entry = feedparser.parse(response.content)['entries'][0]
    assert feed_entry['published'] == publishdate.strftime('%a, %d %b %Y 00:00:00 +0000')
    assert feed_entry['title'] == 'A title'
    assert feed_entry['summary'] == 'A summary'
    assert feed_entry['author'] == 'John Doe'


@pytest.mark.django_db
def test_planet(client: Client) -> None:
    response = client.get('/planet/')
    assert response.status_code == 200

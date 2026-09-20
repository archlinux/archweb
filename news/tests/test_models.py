import pytest
from django.test import Client


@pytest.mark.django_db
def test_feed(client: Client) -> None:
    response = client.get('/feeds/news/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_sitemap(client: Client) -> None:
    response = client.get('/sitemap-news.xml')
    assert response.status_code == 200


@pytest.mark.django_db
def test_news_sitemap(client: Client) -> None:
    response = client.get('/news-sitemap.xml')
    assert response.status_code == 200


@pytest.mark.django_db
def test_newsitem(client: Client) -> None:
    response = client.get('/news/404', follow=True)
    assert response.status_code == 404

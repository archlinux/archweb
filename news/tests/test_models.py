from django.test import Client


def test_feed(db: None, client: Client) -> None:
    response = client.get('/feeds/news/')
    assert response.status_code == 200


def test_sitemap(db: None, client: Client) -> None:
    response = client.get('/sitemap-news.xml')
    assert response.status_code == 200


def test_news_sitemap(db: None, client: Client) -> None:
    response = client.get('/news-sitemap.xml')
    assert response.status_code == 200


def test_newsitem(db: None, client: Client) -> None:
    response = client.get('/news/404', follow=True)
    assert response.status_code == 404

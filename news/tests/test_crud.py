import pytest
from django.core import mail

from news.models import News


def create(admin_client, title='Bash broken', content='Broken in [testing]', announce=False):
    data = {
        'title': title,
        'content': content,
    }
    if announce:
        data['send_announce'] = 'on'
    return admin_client.post('/news/add/', data, follow=True)


@pytest.mark.django_db
def test_create_item(admin_client, admin_user):
    title = 'Bash broken'
    response = create(admin_client, title)
    assert response.status_code == 200

    news = News.objects.first()

    assert news.author == admin_user
    assert news.title == title


@pytest.mark.django_db
def test_view(admin_client):
    create(admin_client)
    news = News.objects.first()

    response = admin_client.get(news.get_absolute_url())
    assert response.status_code == 200


@pytest.mark.django_db
def test_redirect_id(admin_client):
    create(admin_client)
    news = News.objects.first()

    response = admin_client.get(f'/news/{news.id}', follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_send_announce(admin_client):
    title = 'New glibc'
    create(admin_client, title, announce=True)
    assert len(mail.outbox) == 1
    assert title in mail.outbox[0].subject


@pytest.mark.django_db
def test_preview(admin_client):
    response = admin_client.post('/news/preview/', {'data': '**body**'}, follow=True)
    assert response.status_code == 200
    assert response.content.decode() == '<p><strong>body</strong></p>'

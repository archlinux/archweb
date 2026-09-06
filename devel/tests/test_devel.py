import pytest
from django.contrib.auth.models import Group, User

from devel.models import UserProfile


@pytest.fixture
def devel_client(client, arches, repos, package):
    password = 'test'
    user = User.objects.create_superuser('admin',
                                         'admin@archlinux.org',
                                         password)
    for name in ['Developers', 'Retired Developers']:
        Group.objects.create(name=name)
    user.groups.add(Group.objects.get(name='Developers'))
    user.save()
    profile = UserProfile.objects.create(user=user,
                                         public_email=f"{user.username}@awesome.com")
    client.post('/login/', {
        'username': user.username,
        'password': password
    })

    yield client

    profile.delete()
    user.delete()
    Group.objects.all().delete()


def test_clock(devel_client):
    response = devel_client.get('/devel/clock/')
    assert response.status_code == 200


def test_profile(devel_client):
    response = devel_client.get('/devel/profile/')
    assert response.status_code == 200


def test_stats(devel_client):
    response = devel_client.get('/devel/stats/')
    assert response.status_code == 200

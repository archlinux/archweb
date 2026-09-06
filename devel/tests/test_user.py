import pytest
from django.contrib.auth.models import User

from devel.models import UserProfile
from devel.utils import UserFinder


def test_index(client):
    response = client.get('/devel/')
    assert response.status_code == 302
    assert response.has_header('Location')
    assert response['location'] == '/login/?next=/devel/'


def test_profile(client):
    response = client.get('/devel/profile/')
    assert response.status_code == 302
    assert response.has_header('Location')
    assert response['location'] == '/login/?next=/devel/profile/'


def test_newuser(client):
    response = client.get('/devel/newuser/')
    assert response.status_code == 302
    assert response.has_header('Location')
    assert response['location'] == '/login/?next=/devel/newuser/'


def test_mirrors(db, client):
    response = client.get('/mirrors/')
    assert response.status_code == 200


def test_admin_log(db, client):
    User.objects.create_superuser('admin', 'admin@archlinux.org', 'admin')
    response = client.post('/login/', {'username': 'admin', 'password': 'admin'})
    response = client.get('/devel/admin_log', follow=True)
    assert response.status_code == 200


@pytest.fixture
def finder():
    return UserFinder()


@pytest.fixture
def users(transactional_db):
    users = []
    user_profiles = []

    user1 = User.objects.create(
        username="joeuser", first_name="Joe", last_name="User", email="user1@example.com")
    users.append(user1)
    user2 = User.objects.create(
        username="john", first_name="John", last_name="", email="user2@example.com")
    users.append(user2)
    user3 = User.objects.create(
        username="bjones", first_name="Bob", last_name="Jones", email="user3@example.com")
    users.append(user3)

    for user in (user1, user2, user3):
        email_addr = "%s@awesome.com" % user.username
        user_profiles.append(UserProfile.objects.create(user=user, public_email=email_addr))

    user4 = User.objects.create(
        username="tim1", first_name="Tim", last_name="One", email="tim@example.com")
    users.append(user4)
    user5 = User.objects.create(
        username="tim2", first_name="Tim", last_name="Two", email="timtwo@example.com")
    users.append(user5)

    yield users

    for user_profile in user_profiles:
        user_profile.delete()

    for user in users:
        user.delete()


def test_not_matching(finder, users):
    assert finder.find(None) is None
    assert finder.find("") is None
    assert finder.find("Bogus") is None
    assert finder.find("Bogus <invalid") is None
    assert finder.find("Bogus User <bogus@example.com>") is None
    assert finder.find("<bogus@example.com>") is None
    assert finder.find("bogus@example.com") is None
    assert finder.find("Unknown Packager") is None


def test_by_email(finder, users):
    user1, user2, *_ = users
    assert finder.find("XXX YYY <user1@example.com>") == user1
    assert finder.find("YYY ZZZ <user2@example.com>") == user2


def test_by_profile_email(finder, users):
    user1, user2, user3, *_ = users
    assert finder.find("XXX <joeuser@awesome.com>") == user1
    assert finder.find("YYY <john@awesome.com>") == user2
    assert finder.find("ZZZ <bjones@awesome.com>") == user3


def test_by_name(finder, users):
    user1, user2, user3, *_ = users
    assert finder.find("Joe User <joe@differentdomain.com>") == user1
    assert finder.find("Joe User") == user1
    assert finder.find("John <john@differentdomain.com>") == user2
    assert finder.find("John") == user2
    assert finder.find("Bob Jones <bjones AT Arch Linux DOT org>") == user3


def test_by_invalid(finder, users):
    user1, *_ = users
    assert finder.find("Joe User <user1@example.com") == user1
    assert finder.find("Joe 'nickname' User <user1@example.com") == user1
    assert finder.find("Joe \"nickname\" User <user1@example.com") == user1
    assert finder.find("Joe User <joe@differentdomain.com") == user1


def test_cache(finder, users):
    user1, _user2, user3, *_ = users

    # simply look two of them up, but then do it repeatedly
    for _ in range(5):
        assert finder.find("XXX YYY <user1@example.com>") == user1
        assert finder.find("Bob Jones <bjones AT Arch Linux DOT org>") == user3


def test_ambiguous(finder, users):
    _user1, _user2, _user3, user4, user5 = users
    assert finder.find("Tim One <tim@anotherdomain.com>") == user4
    assert finder.find("Tim Two <tim@anotherdomain.com>") == user5
    assert finder.find("Tim <tim@anotherdomain.com>") is None


def test_find_by_username(finder, users):
    user1, *_ = users
    assert finder.find_by_username(None) is None
    assert finder.find_by_username('noone') is None
    assert finder.find_by_username(user1.username) == user1
    # Test cache
    assert finder.find_by_username(user1.username) == user1


def test_find_by_email(finder, users):
    user1, *_ = users
    assert finder.find_by_email(None) is None
    assert finder.find_by_email('bar@bar.com') is None
    assert finder.find_by_email(user1.email) == user1
    # Test cache
    assert finder.find_by_email(user1.email) == user1

# vim: set ts=4 sw=4 et:

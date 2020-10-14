import pytest


from django.contrib.auth.models import User
from devel.utils import UserFinder
from devel.models import UserProfile


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


def test_mirrors(client, db):
    response = client.get('/mirrors/')
    assert response.status_code == 200


def test_admin_log(admin_client):
    response = admin_client.get('/devel/admin_log', follow=True)
    assert response.status_code == 200


@pytest.fixture
def user1(django_user_model):
    user1 = django_user_model.objects.create(username="joeuser", first_name="Joe",
                                             last_name="User", email="user1@example.com")
    email_addr = "%s@awesome.com" % user1.username
    profile = UserProfile.objects.create(user=user1, public_email=email_addr)
    yield user1
    profile.delete()
    user1.delete()


@pytest.fixture
def create_user(django_user_model):
    users = []

    def _create_user(username, firstname, lastname="", email="", public_email=""):
        user = User.objects.create(username=username, first_name=firstname,
                                last_name=lastname, email=email)
        profile = None

        if public_email:
            profile = UserProfile.objects.create(user=user, public_email=public_email)

        users.append((user, profile))
        return user

    yield _create_user

    for user, prof in users:
        if prof:
            prof.delete()
        user.delete()


@pytest.fixture()
def users(create_user):
    create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')
    create_user('john', 'John', '',  'user2@example.com', 'john@awesome.com')
    create_user('bjones', 'Bob', 'Jones',  'user3@example.com', 'bjones@awesome.com')

    create_user('tin1', 'Tim', 'One',  'tim@example.com')
    create_user('tin2', 'Tim', 'Two',  'timtwo@example.com')


@pytest.fixture()
def finder():
    return UserFinder()


def test_not_matching(finder, users):

    assert not finder.find(None)
    assert not finder.find("")
    assert not finder.find("Bogus")
    assert not finder.find("Bogus <invalid")
    assert not finder.find("Bogus User <bogus@example.com>")
    assert not finder.find("<bogus@example.com>")
    assert not finder.find("bogus@example.com")
    assert not finder.find("Unknown Packager")


def test_by_email(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')
    user2 = create_user('john', 'John', '',  'user2@example.com', 'john@example.com')

    assert user1 == finder.find("XXX YYY <user1@example.com>")
    assert user2 == finder.find("YYY ZZZ <user2@example.com>")


def test_by_profile_email(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')
    user2 = create_user('john', 'John', '',  'user2@example.com', 'john@awesome.com')
    user3 = create_user('bjones', 'Bob', 'Jones',  'user3@example.com', 'bjones@awesome.com')

    assert user1 == finder.find("XXX <joeuser@awesome.com>")
    assert user2 == finder.find("YYY <john@awesome.com>")
    assert user3 == finder.find("ZZZ <bjones@awesome.com>")


def test_by_name(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')
    user2 = create_user('john', 'John', '',  'user2@example.com', 'john@awesome.com')
    user3 = create_user('bjones', 'Bob', 'Jones',  'user3@example.com', 'bjones@awesome.com')

    assert user1 == finder.find("Joe User <joe@differentdomain.com>")
    assert user1 == finder.find("Joe User")
    assert user2 == finder.find("John <john@differentdomain.com>")
    assert user2 == finder.find("John")
    assert user3 == finder.find("Bob Jones <bjones AT Arch Linux DOT org>")


def test_by_invalid(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')

    assert user1 == finder.find("Joe User <user1@example.com")
    assert user1 == finder.find("Joe 'nickname' User <user1@example.com")
    assert user1 == finder.find("Joe \"nickname\" User <user1@example.com")
    assert user1 == finder.find("Joe User <joe@differentdomain.com")


def test_cache(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')
    user3 = create_user('bjones', 'Bob', 'Jones',  'user3@example.com', 'bjones@awesome.com')

    # simply look two of them up, but then do it repeatedly
    for _ in range(5):
        assert user1 == finder.find("XXX YYY <user1@example.com>")
        assert user3 == finder.find("Bob Jones <bjones AT Arch Linux DOT org>")


def test_ambiguous(finder, create_user):
    user4 = create_user('tin1', 'Tim', 'One',  'tim@example.com')
    user5 = create_user('tin2', 'Tim', 'Two',  'timtwo@example.com')
    assert user4 == finder.find("Tim One <tim@anotherdomain.com>")
    assert user5 == finder.find("Tim Two <tim@anotherdomain.com>")
    assert not finder.find("Tim <tim@anotherdomain.com>")


def test_find_by_username(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')

    assert not finder.find_by_username(None)
    assert not finder.find_by_username('noone')
    assert user1 == finder.find_by_username(user1.username)
    # Test cache
    assert user1 == finder.find_by_username(user1.username)


def test_find_by_email(finder, create_user):
    user1 = create_user('joeuser', 'Joe', 'User',  'user1@example.com', 'joeuser@awesome.com')

    assert not finder.find_by_email(None)
    assert not finder.find_by_email('bar@bar.com')
    assert user1 == finder.find_by_username(user1.username)
    # Test cache
    assert user1 == finder.find_by_username(user1.username)

# vim: set ts=4 sw=4 et:

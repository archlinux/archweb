import pytest

from django.contrib.auth.models import Group
from django.core.management import call_command

from devel.models import UserProfile


USERNAME = 'joeuser'
FIRSTNAME = 'Joe'
LASTNAME = 'User'
EMAIL = 'user1@example.com'


@pytest.fixture
def arches(db):
    # TODO: create Arch object
    call_command('loaddata', 'main/fixtures/arches.json')


@pytest.fixture
def repos(db):
    # TODO: create Repo object
    call_command('loaddata', 'main/fixtures/repos.json')


@pytest.fixture
def package(db, arches, repos):
    # TODO: convert to create_package with standard parameters
    call_command('loaddata', 'main/fixtures/package.json')


@pytest.fixture
def groups(db):
    call_command('loaddata', 'main/fixtures/groups.json')


@pytest.fixture
def staff_groups(db):
    call_command('loaddata', 'devel/fixtures/staff_groups.json')


@pytest.fixture
def user(django_user_model):
    user = django_user_model.objects.create_user(username=USERNAME, password=USERNAME, email=EMAIL)
    yield user
    user.delete()


@pytest.fixture
def userprofile(user):
    profile = UserProfile.objects.create(user=user,
                                         public_email=f'{user.username}@archlinux.org')
    yield profile
    profile.delete()


@pytest.fixture
def user_client(client, user, userprofile, groups):
    user.groups.add(Group.objects.get(name='Developers'))
    client.login(username=USERNAME, password=USERNAME)
    return client

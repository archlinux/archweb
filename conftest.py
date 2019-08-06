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
    call_command('loaddata', 'main/fixtures/arches.json')


@pytest.fixture
def repos(db):
    call_command('loaddata', 'main/fixtures/repos.json')


@pytest.fixture
def package(db):
    # TODO(jelle): create own parameter based version
    from main.models import Package
    print(list(Package.objects.all()))
    call_command('loaddata', 'main/fixtures/package.json')
    print(list(Package.objects.all()))


@pytest.fixture
def groups(db):
    call_command('loaddata', 'main/fixtures/groups.json')


@pytest.fixture
def staff_groups(db):
    call_command('loaddata', 'devel/fixtures/staff_groups.json')


# TODO: test with non-admin user fixture
@pytest.fixture
def admin_user_profile(admin_user, arches, repos):
    profile = UserProfile.objects.create(user=admin_user,
                                         public_email="public@archlinux.org")
    yield profile
    profile.delete()


@pytest.fixture
def user_client(client, django_user_model, groups):
    user = django_user_model.objects.create_user(username=USERNAME, password=USERNAME)
    profile = UserProfile.objects.create(user=user,
                                         public_email="{}@archlinux.org".format(user.username))
    user.groups.add(Group.objects.get(name='Developers'))
    client.login(username=USERNAME, password=USERNAME)
    yield client
    profile.delete()
    user.delete()

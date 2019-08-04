import pytest

from django.core.management import call_command

from devel.models import UserProfile


@pytest.fixture
def arches(db):
    call_command('loaddata', 'main/fixtures/arches.json')


@pytest.fixture
def repos(db):
    call_command('loaddata', 'main/fixtures/repos.json')


@pytest.fixture
def package(db):
    # TODO(jelle): create own parameter based version
    call_command('loaddata', 'main/fixtures/package.json')


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

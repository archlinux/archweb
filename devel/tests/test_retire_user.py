import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError

from devel.models import UserProfile
from main.models import Repo


@pytest.fixture
def groups():
    for name in ['Developers', 'Retired Developers']:
        Group.objects.create(name=name)


@pytest.fixture
def test_user(arches, repos, groups):
    username = 'joe'
    user = User.objects.create(username=username, first_name="Joe",
                               last_name="User", email="user1@example.com")

    profile = UserProfile.objects.create(user=user,
                                         public_email=f"{user.username}@awesome.com")

    yield user

    profile.delete()
    user.delete()


def test_invalid_args():
    with pytest.raises(CommandError) as e:
        call_command('retire_user')
    assert 'missing argument user.' in str(e)


def test_user_not_found(db):
    with pytest.raises(CommandError) as e:
        call_command('retire_user', 'user1')
    assert "Failed to find User 'user1'" in str(e)


def test_userprofile_missing(db):
    user = User.objects.create(username='user2', first_name="Jane",
                               last_name="User2", email="user2@example.com")

    with pytest.raises(CommandError) as e:
        call_command('retire_user', user.username)
    assert "Failed to find UserProfile" in str(e)
    user.delete()


def test_user_inactive(test_user):
    call_command('retire_user', test_user.username)
    user = User.objects.get(username=test_user.username)
    assert not user.is_active


def test_user_moved_groups(test_user):
    test_user.groups.add(Group.objects.get(name='Developers'))
    test_user.save()

    call_command('retire_user', test_user.username)
    user = User.objects.get(username=test_user.username)
    groups = [Group.objects.get(name='Retired Developers')]
    assert list(user.groups.all()) == groups


def test_user_repos(test_user):
    test_user.userprofile.allowed_repos.add(Repo.objects.get(name='Core'))
    test_user.userprofile.save()

    call_command('retire_user', test_user.username)
    profile = UserProfile.objects.get(user=test_user)
    assert len(profile.allowed_repos.all()) == 0

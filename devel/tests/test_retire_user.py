from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import User, Group
from django.test import TransactionTestCase

from main.models import Repo

from devel.models import UserProfile


class RetireUsertest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']


    def setUp(self):
        self.username = 'joe'
        self.user = User.objects.create(username=self.username, first_name="Joe",
                                         last_name="User", email="user1@example.com")

        self.profile = UserProfile.objects.create(user=self.user,
                                                  public_email="{}@awesome.com".format(self.user.username))
        for name in ['Developers', 'Retired Developers']:
            Group.objects.create(name=name)

    def tearDown(self):
        self.profile.delete()
        self.user.delete()

    def test_invalid_args(self):
        with self.assertRaises(CommandError) as e:
            call_command('retire_user')
        self.assertIn('missing argument user.', str(e.exception))

    def test_user_not_found(self):
        with self.assertRaises(CommandError) as e:
            call_command('retire_user', 'user1')
        self.assertIn("Failed to find User 'user1'", str(e.exception))

    def test_userprofile_missing(self):
        user = User.objects.create(username='user2', first_name="Jane",
                                         last_name="User2", email="user2@example.com")

        with self.assertRaises(CommandError) as e:
            call_command('retire_user', user.username)
        self.assertIn("Failed to find UserProfile", str(e.exception))
        user.delete()

    def test_user_inactive(self):
        call_command('retire_user', self.username)
        user = User.objects.get(username=self.username)
        self.assertEqual(user.is_active, False)

    def test_user_moved_groups(self):
        self.user.groups.add(Group.objects.get(name='Developers'))
        self.user.save()

        call_command('retire_user', self.username)
        user = User.objects.get(username=self.username)
        groups = [Group.objects.get(name='Retired Developers')]
        self.assertEqual(list(user.groups.all()), groups)

    def test_user_repos(self):
        self.profile.allowed_repos.add(Repo.objects.get(name='Core'))
        self.profile.save()

        call_command('retire_user', self.username)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(len(profile.allowed_repos.all()), 0)

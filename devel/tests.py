from django.test import TestCase

from django.contrib.auth.models import User
from devel.utils import find_user
from main.models import UserProfile

class DevelTest(TestCase):
    def test_index(self):
        response = self.client.get('/devel/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/devel/')

    def test_profile(self):
        response = self.client.get('/devel/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/devel/profile/')

    def test_newuser(self):
        response = self.client.get('/devel/newuser/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/devel/newuser/')

    def test_mirrors(self):
        response = self.client.get('/mirrors/')
        self.assertEqual(response.status_code, 200)

class FindUserTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username="joeuser", first_name="Joe",
                last_name="User", email="user1@example.com")
        self.user2 = User.objects.create(username="john", first_name="John",
                last_name="", email="user2@example.com")
        self.user3 = User.objects.create(username="bjones", first_name="Bob",
                last_name="Jones", email="user3@example.com")

        for user in (self.user1, self.user2, self.user3):
            email_addr = "%s@awesome.com" % user.username
            UserProfile.objects.create(user=user, public_email=email_addr)

    def test_not_matching(self):
        self.assertIsNone(find_user(None))
        self.assertIsNone(find_user(""))
        self.assertIsNone(find_user("Bogus"))
        self.assertIsNone(find_user("Bogus <invalid"))
        self.assertIsNone(find_user("Bogus User <bogus@example.com>"))
        self.assertIsNone(find_user("<bogus@example.com>"))
        self.assertIsNone(find_user("bogus@example.com"))
        self.assertIsNone(find_user("Unknown Packager"))

    def test_by_email(self):
        self.assertEqual(self.user1, find_user("XXX YYY <user1@example.com>"))
        self.assertEqual(self.user2, find_user("YYY ZZZ <user2@example.com>"))

    def test_by_profile_email(self):
        self.assertEqual(self.user1, find_user("XXX <joeuser@awesome.com>"))
        self.assertEqual(self.user2, find_user("YYY <john@awesome.com>"))
        self.assertEqual(self.user3, find_user("ZZZ <bjones@awesome.com>"))

    def test_by_name(self):
        self.assertEqual(self.user1, find_user("Joe User <joe@differentdomain.com>"))
        self.assertEqual(self.user1, find_user("Joe User"))
        self.assertEqual(self.user2, find_user("John <john@differentdomain.com>"))
        self.assertEqual(self.user3, find_user("Bob Jones <bjones AT Arch Linux DOT org>"))

# vim: set ts=4 sw=4 et:

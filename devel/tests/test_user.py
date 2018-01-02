from django.contrib.auth.models import User
from django.test import TestCase

from devel.utils import UserFinder
from devel.models import UserProfile

class DevelTest(TestCase):
    def test_index(self):
        response = self.client.get('/devel/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         '/login/?next=/devel/')

    def test_profile(self):
        response = self.client.get('/devel/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         '/login/?next=/devel/profile/')

    def test_newuser(self):
        response = self.client.get('/devel/newuser/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         '/login/?next=/devel/newuser/')

    def test_mirrors(self):
        response = self.client.get('/mirrors/')
        self.assertEqual(response.status_code, 200)

    def test_admin_log(self):
        User.objects.create_superuser('admin', 'admin@archlinux.org', 'admin')
        response = self.client.post('/login/', {'username': 'admin', 'password': 'admin'})
        response = self.client.get('/devel/admin_log', follow=True)
        self.assertEqual(response.status_code, 200)

class FindUserTest(TestCase):

    def setUp(self):
        self.finder = UserFinder()

        self.user1 = User.objects.create(username="joeuser", first_name="Joe",
                last_name="User", email="user1@example.com")
        self.user2 = User.objects.create(username="john", first_name="John",
                last_name="", email="user2@example.com")
        self.user3 = User.objects.create(username="bjones", first_name="Bob",
                last_name="Jones", email="user3@example.com")

        for user in (self.user1, self.user2, self.user3):
            email_addr = "%s@awesome.com" % user.username
            UserProfile.objects.create(user=user, public_email=email_addr)

        self.user4 = User.objects.create(username="tim1", first_name="Tim",
                last_name="One", email="tim@example.com")
        self.user5 = User.objects.create(username="tim2", first_name="Tim",
                last_name="Two", email="timtwo@example.com")

    def test_not_matching(self):
        self.assertIsNone(self.finder.find(None))
        self.assertIsNone(self.finder.find(""))
        self.assertIsNone(self.finder.find("Bogus"))
        self.assertIsNone(self.finder.find("Bogus <invalid"))
        self.assertIsNone(self.finder.find("Bogus User <bogus@example.com>"))
        self.assertIsNone(self.finder.find("<bogus@example.com>"))
        self.assertIsNone(self.finder.find("bogus@example.com"))
        self.assertIsNone(self.finder.find("Unknown Packager"))

    def test_by_email(self):
        self.assertEqual(self.user1,
                self.finder.find("XXX YYY <user1@example.com>"))
        self.assertEqual(self.user2,
                self.finder.find("YYY ZZZ <user2@example.com>"))

    def test_by_profile_email(self):
        self.assertEqual(self.user1,
                self.finder.find("XXX <joeuser@awesome.com>"))
        self.assertEqual(self.user2,
                self.finder.find("YYY <john@awesome.com>"))
        self.assertEqual(self.user3,
                self.finder.find("ZZZ <bjones@awesome.com>"))

    def test_by_name(self):
        self.assertEqual(self.user1,
                self.finder.find("Joe User <joe@differentdomain.com>"))
        self.assertEqual(self.user1,
                self.finder.find("Joe User"))
        self.assertEqual(self.user2,
                self.finder.find("John <john@differentdomain.com>"))
        self.assertEqual(self.user2,
                self.finder.find("John"))
        self.assertEqual(self.user3,
                self.finder.find("Bob Jones <bjones AT Arch Linux DOT org>"))

    def test_by_invalid(self):
        self.assertEqual(self.user1,
                self.finder.find("Joe User <user1@example.com"))
        self.assertEqual(self.user1,
                self.finder.find("Joe 'nickname' User <user1@example.com"))
        self.assertEqual(self.user1,
                self.finder.find("Joe \"nickname\" User <user1@example.com"))
        self.assertEqual(self.user1,
                self.finder.find("Joe User <joe@differentdomain.com"))

    def test_cache(self):
        # simply look two of them up, but then do it repeatedly
        for _ in range(5):
            self.assertEqual(self.user1,
                    self.finder.find("XXX YYY <user1@example.com>"))
            self.assertEqual(self.user3,
                    self.finder.find("Bob Jones <bjones AT Arch Linux DOT org>"))

    def test_ambiguous(self):
        self.assertEqual(self.user4,
                self.finder.find("Tim One <tim@anotherdomain.com>"))
        self.assertEqual(self.user5,
                self.finder.find("Tim Two <tim@anotherdomain.com>"))
        self.assertIsNone(self.finder.find("Tim <tim@anotherdomain.com>"))

# vim: set ts=4 sw=4 et:

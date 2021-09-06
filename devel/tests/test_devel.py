from django.test import TransactionTestCase
from django.contrib.auth.models import User, Group
from devel.models import UserProfile


class DevelView(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser('admin',
                                                  'admin@archlinux.org',
                                                  password)
        for name in ['Developers', 'Retired Developers']:
            Group.objects.create(name=name)
        self.user.groups.add(Group.objects.get(name='Developers'))
        self.user.save()
        self.profile = UserProfile.objects.create(user=self.user,
                                                  public_email="{}@awesome.com".format(self.user.username))
        self.client.post('/login/', {
            'username': self.user.username,
            'password': password
        })

    def tearDown(self):
        self.profile.delete()
        self.user.delete()
        Group.objects.all().delete()

    def test_clock(self):
        response = self.client.get('/devel/clock/')
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        response = self.client.get('/devel/profile/')
        self.assertEqual(response.status_code, 200)
        # Test changing

    def test_stats(self):
        response = self.client.get('/devel/stats/')
        self.assertEqual(response.status_code, 200)

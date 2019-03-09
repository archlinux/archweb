from django.test import TransactionTestCase
from django.contrib.auth.models import User

from main.models import Repo
from packages.models import PackageRelation
from devel.models import UserProfile



class UnFlagPackage(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser('admin',
                                                  'admin@archlinux.org',
                                                  password)
        self.profile = UserProfile.objects.create(user=self.user,
                                                  public_email="{}@awesome.com".format(self.user.username))
        self.profile.allowed_repos.add(Repo.objects.get(name='Core'))
        self.profile.save()
        self.client.post('/login/', {
                                    'username': self.user.username,
                                    'password': password
        })

    def tearDown(self):
        self.profile.delete()
        self.user.delete()
        PackageRelation.objects.all().delete()

    def flag_package(self):
        data = {
            'website': '',
            'email': 'nobody@archlinux.org',
            'message': 'new linux version',
        }
        response = self.client.post('/packages/core/x86_64/linux/flag/',
                                    data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)

    def test_unflag_package_404(self):
        response = self.client.get('/packages/core/x86_64/fooobar/unflag/')
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/packages/core/x86_64/fooobar/unflag/all/')
        self.assertEqual(response.status_code, 404)

    def test_unflag_package(self):
        self.flag_package()
        response = self.client.get('/packages/core/x86_64/linux/unflag/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Flag linux as out-of-date', response.content.decode())

    def test_unflag_all_package(self):
        self.flag_package()
        response = self.client.get('/packages/core/x86_64/linux/unflag/all/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Flag linux as out-of-date', response.content.decode())


class AdoptOrphanPackage(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser('admin',
                                                  'admin@archlinux.org',
                                                  password)
        self.profile = UserProfile.objects.create(user=self.user,
                                                  public_email="{}@awesome.com".format(self.user.username))
        self.profile.allowed_repos.add(Repo.objects.get(name='Core'))
        self.profile.save()
        self.client.post('/login/', {
                                    'username': self.user.username,
                                    'password': password
        })

    def tearDown(self):
        self.profile.delete()
        self.user.delete()
        PackageRelation.objects.all().delete()

    def request(self, pkgid, adopt=True):
        data = {
            'pkgid': pkgid,
        }
        if adopt:
            data['adopt'] = 'adopt'
        else:
            data['disown'] = 'disown'
        return self.client.post('/packages/update/', data, follow=True)

    def test_adopt_package(self):
        pkg = Package.objects.first()
        response = self.request(pkg.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(PackageRelation.objects.all()), 1)

        response = self.request(pkg.id, False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(PackageRelation.objects.all()), 0)

    def test_no_permissions(self):
        self.profile.allowed_repos.set([])
        self.profile.save()
        pkg = Package.objects.first()

        response = self.request(pkg.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(PackageRelation.objects.all()), 0)

    def test_wrong_request(self):
        pkg = Package.objects.first()
        response = self.client.post('/packages/update/', {'pkgid': pkg.id, }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Are you trying to adopt or disown', response.content.decode())

    def test_stale_relations(self):
        response = self.client.get('/packages/stale_relations/')
        self.assertEqual(response.status_code, 200)


class SignOffTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser('admin',
                                                  'admin@archlinux.org',
                                                  password)
        self.profile = UserProfile.objects.create(user=self.user,
                                                  public_email="{}@awesome.com".format(self.user.username))
        self.profile.allowed_repos.add(Repo.objects.get(name='Core'))
        self.profile.save()
        self.client.post('/login/', {
                                    'username': self.user.username,
                                    'password': password
        })

    def tearDown(self):
        self.profile.delete()
        self.user.delete()
        PackageRelation.objects.all().delete()

    def test_signoffs(self):
        response = self.client.get('/packages/signoffs/')
        self.assertEqual(response.status_code, 200)

    def test_signoffs_json(self):
        response = self.client.get('/packages/signoffs/json/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['signoff_groups'], [])


# vim: set ts=4 sw=4 et:

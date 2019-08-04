from django.test import TransactionTestCase
from django.contrib.auth.models import User


class DeveloperReport(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser('admin',
                                                  'admin@archlinux.org',
                                                  password)
        self.client.post('/login/', {
                                    'username': self.user.username,
                                    'password': password
        })

    def tearDown(self):
        self.user.delete()

    def test_overview(self):
        response = self.client.get('/devel/')
        self.assertEqual(response.status_code, 200)

    def test_reports_old(self):
        response = self.client.get('/devel/reports/old', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_outofdate(self):
        response = self.client.get('/devel/reports/long-out-of-date', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_big(self):
        response = self.client.get('/devel/reports/big', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_badcompression(self):
        response = self.client.get('/devel/reports/badcompression', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_uncompressed_man(self):
        response = self.client.get('/devel/reports/uncompressed-man', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_uncompressed_info(self):
        response = self.client.get('/devel/reports/uncompressed-info', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_unneeded_orphans(self):
        response = self.client.get('/devel/reports/unneeded-orphans', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_mismatched_signature(self):
        response = self.client.get('/devel/reports/mismatched-signature', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reports_signature_time(self):
        response = self.client.get('/devel/reports/signature-time', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_non_existing_dependencies(self):
        response = self.client.get('/devel/reports/non-existing-dependencies', follow=True)
        self.assertEqual(response.status_code, 200)

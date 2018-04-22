from django.test import TestCase

from mirrors.models import Mirror, CheckLocation
from mirrors.tests import create_mirror_url


class MirrorUrlTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

    def testAddressFamilies(self):
        self.assertIsNotNone(self.mirror_url.address_families())

    def testHostname(self):
        self.assertEqual(self.mirror_url.hostname, 'archlinux.org')

    def testGetAbsoluteUrl(self):
        absolute_url = self.mirror_url.get_absolute_url()
        expected = '/mirrors/%s/%d/' % (self.mirror_url.mirror.name, self.mirror_url.pk)
        self.assertEqual(absolute_url, expected)

    def test_mirror_overview(self):
        response = self.client.get('/mirrors/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.mirror.name, response.content.decode())

    def testClean(self):
        # TODO: add test for self.mirror_url.clean()
        pass

    def tearDown(self):
        self.mirror_url.delete()


class MirrorTest(TestCase):
    def setUp(self):
        self.mirror = Mirror.objects.create(name='mirror1',
                                            admin_email='admin@archlinux.org')

    def tearDown(self):
        self.mirror.delete()

    def test_downstream(self):
        self.assertEqual(list(self.mirror.downstream()), [])

    def test_get_absolute_url(self):
        absolute_url = self.mirror.get_absolute_url()
        expected = '/mirrors/{}/'.format(self.mirror.name)
        self.assertEqual(absolute_url, expected)

    def test_get_full_url(self):
        self.assertIn(self.mirror.get_absolute_url(), self.mirror.get_full_url())
        self.assertIn('http', self.mirror.get_full_url('http'))


class CheckLocationTest(TestCase):
    def setUp(self):
        self.checkloc = CheckLocation.objects.create(hostname='arch.org',
                                                     source_ip='127.0.0.1',
                                                     country='US')

    def tearDown(self):
        self.checkloc.delete()

    def test_family(self):
        # TODO: mock socket.getaddrinfo in CheckLocation.family
        self.assertIsInstance(self.checkloc.family, int)

    def test_ip_version(self):
        self.assertIsInstance(self.checkloc.ip_version, int)

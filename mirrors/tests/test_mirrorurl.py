from django.test import TestCase

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

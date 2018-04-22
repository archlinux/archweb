from django.test import TestCase

from mirrors.tests import create_mirror_url
from mirrors.models import Mirror


class MirrorListTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

    def tearDown(self):
        self.mirror_url.delete()

    def test_mirrorlist(self):
        response = self.client.get('/mirrorlist/')
        self.assertEqual(response.status_code, 200)

    def test_mirrorlist_tier(self):
        response = self.client.get('/mirrorlist/tier/1/')
        self.assertEqual(response.status_code, 200)

    def test_mirrorlist_tier(self):
        last_tier = Mirror.TIER_CHOICES[-1][0]
        response = self.client.get('/mirrorlist/tier/{}/'.format(last_tier + 1))
        self.assertEqual(response.status_code, 404)

    def test_mirrorlist_all(self):
        response = self.client.get('/mirrorlist/all/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.hostname, response.content.decode())

    def test_mirrorlist_all_http(self):
        response = self.client.get('/mirrorlist/all/http/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.hostname, response.content.decode())

    def test_mirrorlist_all_https(self):
        # First test that without any https mirrors, we get a 404.
        response = self.client.get('/mirrorlist/all/https/')
        self.assertEqual(response.status_code, 404)

        # Now, after adding an HTTPS mirror, we expect to succeed.
        https_mirror_url = create_mirror_url(
            name='https_mirror',
            protocol='https',
            url='https://wikipedia.org')
        response = self.client.get('/mirrorlist/all/https/')
        self.assertEqual(response.status_code, 200)
        https_mirror_url.delete()

    def test_mirrorlist_filter(self):
        jp_mirror_url = create_mirror_url(
            name='jp_mirror',
            country='JP',
            protocol='https',
            url='https://wikipedia.jp')

        # First test that we correctly see the above mirror.
        response = self.client.get('/mirrorlist/?country=JP&protocol=https')
        self.assertEqual(response.status_code, 200)
        self.assertIn(jp_mirror_url.hostname, response.content.decode())

        # Now confirm that the US mirror did not show up.
        self.assertNotIn(self.mirror_url.hostname, response.content.decode())

        jp_mirror_url.delete()

    def test_mirrorlist_status(self):
        response = self.client.get('/mirrorlist/?country=all&use_mirror_status=on')
        self.assertEqual(response.status_code, 200)

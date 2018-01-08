from django.test import TestCase

from mirrors.tests import create_mirror_url


class MirrorListTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

    def tearDown(self):
        self.mirror_url.delete()

    def test_mirrorlist(self):
        response = self.client.get('/mirrorlist/')
        self.assertEqual(response.status_code, 200)

    def test_mirrorlist(self):
        response = self.client.get('/mirrorlist/')
        self.assertEqual(response.status_code, 200)

    def test_mirrorlist_all(self):
        response = self.client.get('/mirrorlist/all/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.hostname, response.content)

    def test_mirrorlist_all_http(self):
        response = self.client.get('/mirrorlist/all/http/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.hostname, response.content)

    def test_mirrorlist_all_https(self):
        response = self.client.get('/mirrorlist/all/https/')
        self.assertEqual(response.status_code, 404)
        # TODO: test 200 case

    def test_mirrorlist_filter(self):
        response = self.client.get('/mirrorlist/?country=all&protocol=http&ip_version=4')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.hostname, response.content)

    def test_generate(self):
        response = self.client.get('/mirrorlist/?country=all&protocol=http&ip_version=4')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mirror_url.hostname, response.content)

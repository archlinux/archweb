import json

from django.test import TestCase

from mirrors.models import MirrorUrl, MirrorProtocol, Mirror

def create_mirror_url():
        mirror = Mirror.objects.create(name='mirror1', admin_email='admin@archlinux.org')
        mirror_protocol = MirrorProtocol.objects.create(protocol='http')
        mirror_url = MirrorUrl.objects.create(url='https://archlinux.org', protocol=mirror_protocol,
                mirror=mirror, country='US')
        return mirror_url

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
        self.assertIn(self.mirror_url.mirror.name, response.content)

    def testClean(self):
        # TODO: add test for self.mirror_url.clean()
        pass

    def tearDown(self):
        self.mirror_url.delete()

class MirrorStatusTest(TestCase):
    def test_status(self):
        response = self.client.get('/mirrors/status/')
        self.assertEqual(response.status_code, 200)

    def test_json_endpoint(self):
        response = self.client.get('/mirrors/status/json/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['urls'], [])

        mirror_url = create_mirror_url()

        # Verify that the cache works
        response = self.client.get('/mirrors/status/json/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Disables the cache_function's cache
        with self.settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
            response = self.client.get('/mirrors/status/json/')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(len(data['urls']), 1)
            mirror = data['urls'][0]
            self.assertEqual(mirror['url'], mirror_url.url)


class MirrorListTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

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

from django.test import TestCase

from mirrors.tests import create_mirror_url


class MirrorStatusTest(TestCase):
    def test_status(self):
        response = self.client.get('/mirrors/status/')
        self.assertEqual(response.status_code, 200)

    def test_json_endpoint(self):
        # Disables the cache_function's cache
        with self.settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
            response = self.client.get('/mirrors/status/json/')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['urls'], [])

            mirror_url = create_mirror_url()

            response = self.client.get('/mirrors/status/json/')
            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertEqual(len(data['urls']), 1)
            mirror = data['urls'][0]
            self.assertEqual(mirror['url'], mirror_url.url)

        mirror_url.delete()

    def test_json_tier(self):
        response = self.client.get('/mirrors/status/tier/99/json/')
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/mirrors/status/tier/1/json/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['urls'], [])

        mirror_url = create_mirror_url()

        # Disables the cache_function's cache
        with self.settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
            response = self.client.get('/mirrors/status/json/')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertNotEqual(data['urls'], [])

        mirror_url.delete()

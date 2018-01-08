import json

from django.test import TestCase

from mirrors.tests import create_mirror_url


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

        mirror_url.delete()

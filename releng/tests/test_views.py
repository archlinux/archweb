from django.test import TestCase

from releng.models import Release


class RelengViewTest(TestCase):
    fixtures = ['releng/fixtures/release.json']

    def setUp(self):
        self.release = Release.objects.first()

    def test_release_json(self):
        version = self.release.version
        response = self.client.get('/releng/releases/json/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['version'], 1)
        release = data['releases'][0]
        self.assertEqual(release['version'], version)

    def test_netboot_page(self):
        response = self.client.get('/releng/netboot/')
        self.assertEqual(response.status_code, 200)

    def test_release_torrent_not_found(self):
        # TODO: Add torrent data to release fixture
        version = self.release.version
        response = self.client.get('/releng/releases/{}/torrent/'.format(version))
        self.assertEqual(response.status_code, 404)

    def test_release_details(self):
        version = self.release.version
        response = self.client.get('/releng/releases/{}/'.format(version))
        self.assertEqual(response.status_code, 200)
        self.assertIn(version, response.content.decode('utf-8'))

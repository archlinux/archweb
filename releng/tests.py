import hashlib
from datetime import datetime

from django.test import TestCase

from releng.models import Release


class RelengTest(TestCase):
    fixtures = ['releng/fixtures/release.json']

    def setUp(self):
        self.release = Release.objects.first()

    def test_feed(self):
        response = self.client.get('/feeds/releases/')
        self.assertEqual(response.status_code, 200)

    def test_absolute_url(self):
        self.assertIn(self.release.version, self.release.get_absolute_url())

    def test_iso_url(self):
        url = self.release.iso_url()
        ver = self.release.version
        expected = 'iso/{}/archlinux-{}-x86_64.iso'.format(ver, ver)
        self.assertEqual(url, expected)

    def test_info_html(self):
        self.assertIn(self.release.info, self.release.info_html())

    def test_dir_path(self):
        dir_path = u'iso/{}/'.format(self.release.version)
        self.assertEqual(dir_path, self.release.dir_path())

    def test_sitemap(self):
        response = self.client.get('/sitemap-releases.xml')
        self.assertEqual(response.status_code, 200)

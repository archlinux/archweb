import json
import unittest

from django.test import TestCase

from .alpm import AlpmAPI


alpm = AlpmAPI()


class AlpmTestCase(unittest.TestCase):

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_version(self):
        version = alpm.version()
        self.assertIsNotNone(version)
        version = version.split('.')
        # version is a 3-tuple, e.g., '7.0.2'
        self.assertEqual(3, len(version))

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_vercmp(self):
        self.assertEqual(0, alpm.vercmp("1.0", "1.0"))
        self.assertEqual(1, alpm.vercmp("1.1", "1.0"))

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_compare_versions(self):
        self.assertTrue(alpm.compare_versions("1.0", "<=", "2.0"))
        self.assertTrue(alpm.compare_versions("1.0", "<", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0", ">=", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0", ">", "2.0"))
        self.assertTrue(alpm.compare_versions("1:1.0", ">", "2.0"))
        self.assertFalse(alpm.compare_versions("1.0.2", ">=", "2.1.0"))

        self.assertTrue(alpm.compare_versions("1.0", "=", "1.0"))
        self.assertTrue(alpm.compare_versions("1.0", "=", "1.0-1"))
        self.assertFalse(alpm.compare_versions("1.0", "!=", "1.0"))

    def test_behavior_when_unavailable(self):
        mock_alpm = AlpmAPI()
        mock_alpm.available = False

        self.assertIsNone(mock_alpm.version())
        self.assertIsNone(mock_alpm.vercmp("1.0", "1.0"))
        self.assertIsNone(mock_alpm.compare_versions("1.0", "=", "1.0"))


class PackagesTest(TestCase):

    def test_feed(self):
        response = self.client.get('/feeds/packages/')
        self.assertEqual(response.status_code, 200)

    def test_sitemap(self):
        for sitemap in ['packages', 'package-groups', 'package-files', 'split-packages']:
            response = self.client.get('/sitemap-{}.xml'.format(sitemap))
            self.assertEqual(response.status_code, 200)


class PackageSearchJson(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']


    def test_invalid(self):
        response = self.client.get('/packages/search/json/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['limit'], 250)
        self.assertEqual(data['results'], [])
        self.assertEqual(data['valid'], False)

    def test_reponame(self):
        response = self.client.get('/packages/search/json/?repository=core')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['pkgname'], 'linux')

    def test_packagename(self):
        response = self.client.get('/packages/search/json/?name=linux')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)

    def test_no_results(self):
        response = self.client.get('/packages/search/json/?name=none')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 0)


class PackageSearch(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_invalid(self):
        response = self.client.get('/packages/?q=test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content)

    def test_exact_match(self):
        response = self.client.get('/packages/?q=linux')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content)

    def test_filter_name(self):
        response = self.client.get('/packages/?name=name')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content)

    def test_filter_repo(self):
        response = self.client.get('/packages/?repo=Core')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content)

    def test_filter_desc(self):
        response = self.client.get('/packages/?desc=kernel')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content)

    def test_filter_flagged(self):
        response = self.client.get('/packages/?flagged=Flagged')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content)

    def test_filter_not_flagged(self):
        response = self.client.get('/packages/?flagged=Not Flagged')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content)

    def test_filter_arch(self):
        response = self.client.get('/packages/?arch=any')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content)

    def test_filter_maintainer_orphan(self):
        response = self.client.get('/packages/?maintainer=orphan')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content)

    def test_filter_packager_unknown(self):
        response = self.client.get('/packages/?packager=unknown')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content)

# vim: set ts=4 sw=4 et:

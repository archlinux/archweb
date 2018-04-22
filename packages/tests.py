import json
import unittest

from django.core import mail
from django.test import TestCase

from .alpm import AlpmAPI


alpm = AlpmAPI()


class AlpmTestCase(unittest.TestCase):

    @unittest.skipUnless(alpm.available, "ALPM is unavailable")
    def test_version(self):
        version = alpm.version()
        self.assertIsNotNone(version)
        version = version.split(b'.')
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
        data = json.loads(response.content.decode())
        self.assertEqual(data['limit'], 250)
        self.assertEqual(data['results'], [])
        self.assertEqual(data['valid'], False)

    def test_reponame(self):
        response = self.client.get('/packages/search/json/?repository=core')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['results']), 5)
        self.assertEqual(set([r['pkgname'] for r in data['results']]),
                         {"coreutils", "glibc", "linux", "pacman", "systemd"})

    def test_packagename(self):
        response = self.client.get('/packages/search/json/?name=linux')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['results']), 1)

    def test_no_results(self):
        response = self.client.get('/packages/search/json/?name=none')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data['results']), 0)

    def test_limit_four(self):
        response = self.client.get('/packages/search/json/?limit=4')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['num_pages'], 2)
        self.assertEqual(data['limit'], 4)
        self.assertEqual(len(data['results']), 4)

    def test_second_page(self):
        response = self.client.get('/packages/search/json/?limit=4&page=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data['page'], 2)
        self.assertEqual(data['num_pages'], 2)
        self.assertEqual(len(data['results']), 1)


class PackageSearch(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_invalid(self):
        response = self.client.get('/packages/?q=test')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content.decode())

    def test_exact_match(self):
        response = self.client.get('/packages/?q=linux')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content.decode())

    def test_filter_name(self):
        response = self.client.get('/packages/?name=name')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content.decode())

    def test_filter_repo(self):
        response = self.client.get('/packages/?repo=Core')
        self.assertEqual(response.status_code, 200)
        self.assertIn('5 matching packages found', response.content.decode())

    def test_filter_desc(self):
        response = self.client.get('/packages/?desc=kernel')
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 matching package found', response.content.decode())

    def test_filter_flagged(self):
        response = self.client.get('/packages/?flagged=Flagged')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content.decode())

    def test_filter_not_flagged(self):
        response = self.client.get('/packages/?flagged=Not Flagged')
        self.assertEqual(response.status_code, 200)
        self.assertIn('5 matching packages found', response.content.decode())

    def test_filter_arch(self):
        response = self.client.get('/packages/?arch=any')
        self.assertEqual(response.status_code, 200)
        self.assertIn('0 matching packages found', response.content.decode())

    def test_filter_maintainer_orphan(self):
        response = self.client.get('/packages/?maintainer=orphan')
        self.assertEqual(response.status_code, 200)
        self.assertIn('5 matching packages found', response.content.decode())

    def test_filter_packager_unknown(self):
        response = self.client.get('/packages/?packager=unknown')
        self.assertEqual(response.status_code, 200)
        self.assertIn('5 matching packages found', response.content.decode())

class OpenSearch(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_packages(self):
        response = self.client.get('/opensearch/packages/')
        self.assertEqual(response.status_code, 200)

    def test_packages_suggest(self):
        response = self.client.get('/opensearch/packages/suggest?q=linux')
        self.assertEqual(response.status_code, 200)
        self.assertIn('linux', response.content.decode())

        response = self.client.get('/opensearch/packages/suggest')

class PackageViews(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_arch_differences(self):
        response = self.client.get('/packages/differences/')
        self.assertEqual(response.status_code, 200)


class PackageDisplay(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_packages_detail(self):
        response = self.client.get('/packages/core/x86_64/linux/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/packages/core/x86_64/nope/')
        self.assertEqual(response.status_code, 404)

        # Redirect to search
        response = self.client.get('/packages/core/x86_64/')
        self.assertEqual(response.status_code, 302)

    def test_packages_json(self):
        response = self.client.get('/packages/core/x86_64/linux/json/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data['pkgbase'], 'linux')
        # TODO verify more of the structure

    def test_packages_files(self):
        response = self.client.get('/packages/core/x86_64/linux/files/')
        self.assertEqual(response.status_code, 200)

    def test_packages_files_json(self):
        response = self.client.get('/packages/core/x86_64/linux/files/json/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data['pkgname'], 'linux')
        # TODO verify more of the structure

    def test_packages_download(self):
        response = self.client.get('/packages/core/x86_64/linux/download/')
        self.assertEqual(response.status_code, 404)
        # TODO: Figure out how to fake a mirror

    def test_groups(self):
        response = self.client.get('/groups/')
        self.assertEqual(response.status_code, 200)

    def test_groups_detail(self):
        response = self.client.get('/groups/x86_64/base/')
        self.assertEqual(response.status_code, 404)
        # FIXME: add group fixtures.


class FlagPackage(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_flag_package(self):
        data = {
            'website': '',
            'email': 'nobody@archlinux.org',
            'message': 'new linux version',
        }
        response = self.client.post('/packages/core/x86_64/linux/flag/',
                                    data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Package Flagged - linux', response.content.decode())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('package [linux] marked out-of-date', mail.outbox[0].subject)

        # Flag again, should fail
        response = self.client.post('/packages/core/x86_64/linux/flag/',
                                    data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('has already been flagged out-of-date.', response.content.decode())

    def test_flag_package_invalid(self):
        data = {
            'website': '',
            'email': 'nobody@archlinux.org',
            'message': 'a',
        }
        response = self.client.post('/packages/core/x86_64/linux/flag/',
                                    data,
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Enter a valid and useful out-of-date message', response.content.decode())
        self.assertEqual(len(mail.outbox), 0)


# vim: set ts=4 sw=4 et:

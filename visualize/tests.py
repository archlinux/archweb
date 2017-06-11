from django.test import TestCase


class VisualeTest(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def test_urls(self):
        for url in ['', 'by_repo/', 'by_arch/']:
            response = self.client.get('/visualize/{}'.format(url))
            self.assertEqual(response.status_code, 200)

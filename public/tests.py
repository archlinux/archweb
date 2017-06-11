from django.test import TestCase


class PublicTest(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json', 'main/fixtures/groups.json',
                'devel/fixtures/staff_groups.json']

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_art(self):
        response = self.client.get('/art/')
        self.assertEqual(response.status_code, 200)

    def test_svn(self):
        response = self.client.get('/svn/')
        self.assertEqual(response.status_code, 200)

    def test_developers_old(self):
        response = self.client.get('/developers/')
        self.assertEqual(response.status_code, 301)

    def test_fellows_old(self):
        response = self.client.get('/fellows/')
        self.assertEqual(response.status_code, 301)

    def test_donate(self):
        response = self.client.get('/donate/')
        self.assertEqual(response.status_code, 200)

    def test_download(self):
        response = self.client.get('/download/')
        self.assertEqual(response.status_code, 200)

    def test_master_keys(self):
        response = self.client.get('/master-keys/')
        self.assertEqual(response.status_code, 200)

    def test_master_keys_json(self):
        response = self.client.get('/master-keys/json/')
        self.assertEqual(response.status_code, 200)

    def test_feeds(self):
        response = self.client.get('/feeds/')
        self.assertEqual(response.status_code, 200)

    def test_people(self):
        response = self.client.get('/people/developers/')
        self.assertEqual(response.status_code, 200)

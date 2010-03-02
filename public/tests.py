from django.test import TestCase


class PublicTest(TestCase):

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

    def test_developers(self):
        response = self.client.get('/developers/')
        self.assertEqual(response.status_code, 200)

    def test_fellows(self):
        response = self.client.get('/fellows/')
        self.assertEqual(response.status_code, 200)

    def test_donate(self):
        response = self.client.get('/donate/')
        self.assertEqual(response.status_code, 200)

    def test_download(self):
        response = self.client.get('/download/')
        self.assertEqual(response.status_code, 200)


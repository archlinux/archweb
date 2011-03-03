from django.test import TestCase


class DevelTest(TestCase):

    def test_index(self):
        response = self.client.get('/devel/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/devel/')

    def test_profile(self):
        response = self.client.get('/devel/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/devel/profile/')

    def test_newuser(self):
        response = self.client.get('/devel/newuser/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/devel/newuser/')

    def test_mirrors(self):
        response = self.client.get('/mirrors/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.has_header('Location'), True)
        self.assertEqual(response['location'],
                         'http://testserver/login/?next=/mirrors/')

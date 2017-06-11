from django.test import TestCase

class RelengTest(TestCase):

    def test_feed(self):
        response = self.client.get('/feeds/releases/')
        self.assertEqual(response.status_code, 200)

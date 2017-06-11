from django.test import TestCase

class NewTest(TestCase):

    def test_feed(self):
        response = self.client.get('/feeds/news/')
        self.assertEqual(response.status_code, 200)

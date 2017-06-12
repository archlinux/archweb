from django.test import TestCase

class NewTest(TestCase):

    def test_feed(self):
        response = self.client.get('/feeds/news/')
        self.assertEqual(response.status_code, 200)

    def test_sitemap(self):
        response = self.client.get('/sitemap-news.xml')
        self.assertEqual(response.status_code, 200)

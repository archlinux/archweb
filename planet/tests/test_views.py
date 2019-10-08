from django.test import TestCase


class PlanetTest(TestCase):

    def test_feed(self):
        response = self.client.get('/feeds/planet/')
        self.assertEqual(response.status_code, 200)

    def test_planet(self):
        response = self.client.get('/planet/')
        self.assertEqual(response.status_code, 200)

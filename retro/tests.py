from django.test import TestCase

from retro.views import RETRO_YEAR_MAP

class RetroTest(TestCase):

    def test_404(self):
        response = self.client.get('/retro/1999/')
        self.assertEqual(response.status_code, 404)

    def test_retro(self):
        for year, _ in RETRO_YEAR_MAP.items():
            response = self.client.get('/retro/{}/'.format(year))
            self.assertEqual(response.status_code, 200)

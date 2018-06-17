from django.test import TestCase

from mirrors.models import CheckLocation


class MirrorLocationsTest(TestCase):
    def setUp(self):
        self.checklocation = CheckLocation.objects.create(hostname='arch.org',
                                                          source_ip='8.8.8.8',
                                                          country='US')

    def test_mirrorlocations_json(self):
        response = self.client.get('/mirrors/locations/json/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(1, data['version'])
        location = data['locations'][0]['country_code']
        self.assertEqual('US', location)

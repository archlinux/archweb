from django.test import TestCase


from main.templatetags.flags import country_flag
from mirrors.models import CheckLocation


class FlagsTemplateTest(TestCase):

    def setUp(self):
        self.checkloc = CheckLocation.objects.create(hostname='arch.org',
                                                     source_ip='127.0.0.1',
                                                     country='US')

    def tearDown(self):
        self.checkloc.delete()

    def test_country_flag(self):
        flag = country_flag(self.checkloc.country)
        self.assertIn(self.checkloc.country.name, flag)
        self.assertIn(self.checkloc.country.code.lower(), flag)

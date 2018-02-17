from django.test import SimpleTestCase


from main.management.commands.donor_import import Command


class DonorImportTest(SimpleTestCase):

    def setUp(self):
        self.command = Command()

    def gen_parse_subject(self, data):
        return self.command.parse_subject(valid.format(data))

    def test_parse_subject(self):
        self.assertIsNone(self.command.parse_subject('garbage'))

        # Valid
        valid = u'Receipt [$25.00] By: John Doe [john.doe@archlinux.org]'
        output = self.command.parse_subject(valid)
        self.assertEqual(output, u'John Doe')


    def test_parse_name(self):
        self.assertEqual(self.command.sanitize_name(u'1244'), u'')
        self.assertEqual(self.command.sanitize_name(u'John Doe'), u'John Doe')
        self.assertEqual(self.command.sanitize_name(u' John Doe '), u'John Doe')
        self.assertEqual(self.command.sanitize_name(u'John Doe 23'), u'John Doe')

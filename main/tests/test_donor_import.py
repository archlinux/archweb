# -*- coding: utf-8 -*-

from email.header import Header

from django.test import SimpleTestCase
from django.core.management import call_command
from django.core.management.base import CommandError


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

    def test_decode_subject(self):
        text = u'メイル'
        subject = Header(text, 'utf-8')
        self.assertEqual(self.command.decode_subject(subject), text)

    def test_invalid_args(self):
        with self.assertRaises(CommandError) as e:
            call_command('donor_import')
        self.assertIn('Error: the following arguments are required', str(e.exception))

    def test_invalid_path(self):
        with self.assertRaises(CommandError) as e:
            call_command('donor_import', '/tmp/non-existant')
        self.assertIn('Failed to open maildir', str(e.exception))

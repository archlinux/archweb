# -*- coding: utf-8 -*-

import sys
from email.header import Header
from email.message import Message
from io import StringIO
from tempfile import mkdtemp

from django.test import TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from main.models import Donor
from main.management.commands.donor_import import Command


class DonorImportTest(TransactionTestCase):

    def setUp(self):
        self.command = Command()

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
        stdin = sys.stdin
        with self.assertRaises(CommandError) as e:
            sys.stdin = StringIO('')
            call_command('donor_import')
        self.assertIn('Failed to read from STDIN', str(e.exception))
        sys.stdin = stdin

    def test_invalid_path(self):
        with self.assertRaises(CommandError) as e:
            call_command('donor_import', '/tmp/non-existant')
        self.assertIn('argument input: can\'t open', str(e.exception))

    def test_import(self):
        tmpmail = mkdtemp('archweb') + "/mail"

        msg = Message()
        msg['subject'] = 'John Doe'
        msg['to'] = 'John Doe <john@doe.com>'
        with open(tmpmail, 'wb') as fp:
            fp.write(msg.as_bytes())

        # Invalid
        with self.assertRaises(SystemExit):
            call_command('donor_import', tmpmail)
        self.assertEqual(len(Donor.objects.all()), 0)

        # Valid
        msg = Message()
        msg['subject'] = 'Receipt [$25.00] By: David Doe [david@doe.com]'
        msg['to'] = 'John Doe <david@doe.com>'
        with open(tmpmail, 'wb') as fp:
            fp.write(msg.as_bytes())

        call_command('donor_import', tmpmail)
        self.assertEqual(len(Donor.objects.all()), 1)

        # Re-running should result in no new donor
        call_command('donor_import', tmpmail)
        self.assertEqual(len(Donor.objects.all()), 1)

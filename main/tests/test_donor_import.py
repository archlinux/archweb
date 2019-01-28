# -*- coding: utf-8 -*-

from email.header import Header
from email.message import Message
from mailbox import Maildir
from tempfile import mkdtemp
from shutil import rmtree

from django.test import TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from main.models import Donor
from main.management.commands.donor_import import Command


class DonorImportTest(TransactionTestCase):

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

    def test_maildir(self):
        tmpdir = mkdtemp('archweb')
        mdir = tmpdir + '/maildir'

        maildir = Maildir(mdir)
        msg = Message()
        msg['subject'] = 'John Doe'
        msg['to'] = 'John Doe <john@doe.com>'
        maildir.add(msg)

        # Invalid
        call_command('donor_import', mdir)
        self.assertEqual(len(Donor.objects.all()), 0)

        # Valid
        msg = Message()
        msg['subject'] = 'Receipt [$25.00] By: David Doe [david@doe.com]'
        msg['to'] = 'John Doe <david@doe.com>'
        maildir.add(msg)
        call_command('donor_import', mdir)
        self.assertEqual(len(Donor.objects.all()), 1)

        # Re-running should result in no new donor
        call_command('donor_import', mdir)
        self.assertEqual(len(Donor.objects.all()), 1)

        rmtree(tmpdir)

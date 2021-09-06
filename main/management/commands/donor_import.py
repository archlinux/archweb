# -*- coding: utf-8 -*-
"""
donor_import

Imports donators from the emails which are send to donate@archlinux.org,
the subject of them email contains the name of the donator, the amount and
the email address. Archweb's Donate model only contains the name, which is
unique.

An example subject:

Subject: Receipt [$25.00] By: John Doe [john.doe@archlinux.org]

Usage: cat mail.eml| ./manage.py donor_import
Usage: As it takes an email on stdin, this can be used as a mda command in e.g. fetchmail.
"""

import codecs
import logging
import email
import sys

from email.header import decode_header

from parse import parse
from argparse import FileType

from django.db.utils import Error as DBError
from django.core.management.base import BaseCommand, CommandError
from main.models import Donor


logging.basicConfig(
    level=logging.WARNING,
    format=u'%(asctime)s -> %(levelname)s: %(message)s',
    datefmt=u'%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('input', nargs='?', type=FileType('r'), default=sys.stdin)

    def decode_subject(self, subject):
        subject = decode_header(subject)
        default_charset = 'utf-8'
        # Convert the list of tuples containing the decoded string and encoding to
        # UTF-8
        return ''.join([codecs.decode(s[0], s[1] or default_charset) for s in subject])

    def parse_subject(self, subject):
        """Format of the subject is as following: Receipt [$amount] By: John Doe [mail]"""

        parsed = parse("Receipt [{amount}] By: {name} [{email}]", subject)

        if parsed:
            return parsed['name']

    def sanitize_name(self, name):
        """Sanitizes the parsed name and removes numbers, entries with no
        valid characters and finally trims all excess whitespace"""

        # Some submissions contain no alphabetic characters, skip them
        if all(not l.isalpha() for l in name):
            return u''

        # Strip any numbers, they could be a bank account number
        name = u''.join([l for l in name if not l.isdigit()])

        # Normalize all capitalized names. (JOHN DOE)
        name = u' '.join(l.capitalize() for l in name.split(u' '))

        # Trim excess spaces
        name = name.rstrip().lstrip()

        return name

    def handle(self, *args, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        msg = email.message_from_file(options['input'])
        if not msg['subject']:
            raise CommandError(u"Failed to read from STDIN")
        subject = msg.get('subject', '')
        if 'utf-8' in subject:
            # Decode UTF-8 encoded subjects
            subject = self.decode_subject(subject)

        # Subject header can contain enters, replace them with a space
        subject = subject.replace(u'\n', u' ')

        name = self.parse_subject(subject)
        if not name:
            logger.error(u'Unable to parse: %s', subject)
            sys.exit(0)

        name = self.sanitize_name(name)
        if not name:
            logger.error(u'Invalid name in subject: %s', subject)
            sys.exit(0)

        try:
            _, created = Donor.objects.get_or_create(name=name)
            if created:
                logger.info(u'Adding donor: {}'.format(name))
        except DBError as e:
            logger.info(u'Error while adding donor: %s, %s', name, e)

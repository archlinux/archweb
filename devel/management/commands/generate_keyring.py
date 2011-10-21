# -*- coding: utf-8 -*-
"""
generate_keyring command

Assemble a GPG keyring with all known developer keys.

Usage: ./manage.py generate_keyring <keyserver> <keyring_path>
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

import logging
import subprocess
import sys

from main.models import UserProfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(BaseCommand):
    args = "<keyserver> <keyring_path>"
    help = "Assemble a GPG keyring with all known developer keys."

    def handle(self, *args, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v == 2:
            logger.level = logging.DEBUG

        if len(args) != 2:
            raise CommandError("keyserver and keyring_path must be provided")

        return generate_keyring(args[0], args[1])

def generate_keyring(keyserver, keyring):
    logger.info("getting all known key IDs")

    exclude = Q(pgp_key__isnull=True) & Q(pgp_key__exact="")
    key_ids = UserProfile.objects.exclude(
            exclude).values_list("pgp_key", flat=True)
    logger.info("%d keys fetched from user profiles", len(key_ids))

    gpg_cmd = ["gpg", "--no-default-keyring", "--keyring", keyring,
            "--keyserver", keyserver, "--recv-keys"]
    logger.info("running command: %r", gpg_cmd)
    gpg_cmd.extend(key_ids)
    subprocess.check_call(gpg_cmd)
    logger.info("keyring at %s successfully updated", keyring)

# vim: set ts=4 sw=4 et:

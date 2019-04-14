# -*- coding: utf-8 -*-
"""
generate_keyring command

Assemble a GPG keyring with all known developer keys.

Usage: ./manage.py generate_keyring <keyserver> <keyring_path>
"""

from django.core.management.base import CommandError

import subprocess

from main.management.command import BaseCommand
from devel.models import MasterKey, UserProfile

class Command(BaseCommand):
    args = "<keyserver> <keyring_path> [ownertrust_path]"
    help = "Assemble a GPG keyring with all known developer keys."

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*', help='<arch> <filename>')

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError("keyserver and keyring_path must be provided")

        self.generate_keyring(args[0], args[1])

        if len(args) > 2:
            self.generate_ownertrust(args[2])

    def generate_keyring(self, keyserver, keyring):
        self.logger.info("getting all known key IDs")

        # Screw you Django, for not letting one natively do value != <empty string>
        key_ids = UserProfile.objects.filter(
                pgp_key__isnull=False).extra(where=["pgp_key != ''"]).values_list(
                "pgp_key", flat=True)
        self.logger.info("%d keys fetched from user profiles", len(key_ids))
        master_key_ids = MasterKey.objects.values_list("pgp_key", flat=True)
        self.logger.info("%d keys fetched from master keys", len(master_key_ids))

        # GPG is stupid and interprets any filename without path portion as being
        # in ~/.gnupg/. Fake it out if we just get a bare filename.
        if '/' not in keyring:
            keyring = './%s' % keyring
        gpg_cmd = ["gpg", "--no-default-keyring", "--keyring", keyring,
                "--keyserver", keyserver, "--recv-keys"]
        self.logger.info("running command: %r", gpg_cmd)
        gpg_cmd.extend(key_ids)
        gpg_cmd.extend(master_key_ids)
        subprocess.check_call(gpg_cmd)
        self.logger.info("keyring at %s successfully updated", keyring)

    def generate_ownertrust(self, trust_path):
        master_key_ids = MasterKey.objects.values_list("pgp_key", flat=True)
        with open(trust_path, "w") as trustfile:
            for key_id in master_key_ids:
                trustfile.write("%s:%d:\n" % (key_id, TRUST_LEVELS['marginal']))
        self.logger.info("trust file at %s created or overwritten", trust_path)


TRUST_LEVELS = {
    'unknown': 0,
    'expired': 1,
    'undefined': 2,
    'never': 3,
    'marginal': 4,
    'fully': 5,
    'ultimate': 6,
}

# vim: set ts=4 sw=4 et:

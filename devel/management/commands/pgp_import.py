# -*- coding: utf-8 -*-
"""
pgp_import command

Import keys and signatures from a given GPG keyring.

Usage: ./manage.py pgp_import <keyring_path>
"""

from collections import OrderedDict
from datetime import datetime
import logging
from pytz import utc
import subprocess
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from devel.models import DeveloperKey, PGPSignature
from devel.utils import UserFinder


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(BaseCommand):
    args = "<keyring_path>"
    help = "Import keys and signatures from a given GPG keyring."

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*', help='<arch> <filename>')

    def handle(self, *args, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        if len(args) < 1:
            raise CommandError("keyring_path must be provided")

        import_keys(args[0])
        import_signatures(args[0])


def get_date(epoch_string):
    '''Convert a epoch string into a python 'date' object (not datetime).'''
    if not epoch_string:
        return None
    return datetime.utcfromtimestamp(int(epoch_string)).date()


def get_datetime(epoch_string):
    '''Convert a epoch string into a python 'datetime' object.'''
    if not epoch_string:
        return None
    return datetime.utcfromtimestamp(int(epoch_string)).replace(tzinfo=utc)


def call_gpg(keyring, *args):
    # GPG is stupid and interprets any filename without path portion as being
    # in ~/.gnupg/. Fake it out if we just get a bare filename.
    if '/' not in keyring:
        keyring = './%s' % keyring
    gpg_cmd = ["gpg2", "--no-default-keyring", "--keyring", keyring,
            "--with-colons", "--fixed-list-mode"]
    gpg_cmd.extend(args)
    logger.info("running command: %s", ' '.join(gpg_cmd))
    proc = subprocess.Popen(gpg_cmd, stdout=subprocess.PIPE)
    outdata, errdata = proc.communicate()
    if proc.returncode != 0:
        logger.error(errdata)
        raise subprocess.CalledProcessError(proc.returncode, gpg_cmd)
    return outdata


class KeyData(object):
    def __init__(self, key, created, expires):
        self.key = key
        self.created = get_datetime(created)
        self.expires = get_datetime(expires)
        self.parent = None
        self.revoked = None
        self.db_id = None


def parse_keydata(data):
    keys = OrderedDict()
    current_pubkey = None

    # parse all of the output from our successful GPG command
    logger.info("parsing command output")
    node = None
    for line in data.split('\n'):
        parts = line.split(':')
        if parts[0] == 'pub':
            key = parts[4]
            current_pubkey = key
            keys[key] = KeyData(key, parts[5], parts[6])
            node = parts[0]
        elif parts[0] == 'sub':
            key = parts[4]
            keys[key] = KeyData(key, parts[5], parts[6])
            keys[key].parent = current_pubkey
            node = parts[0]
        elif parts[0] == 'uid':
            node = parts[0]
        elif parts[0] == 'rev' and node in ('pub', 'sub'):
            keys[current_pubkey].revoked = get_datetime(parts[5])

    return keys


def find_key_owner(key, keys, finder):
    '''Recurse up the chain, looking for an owner.'''
    if key is None:
        return None
    owner = finder.find_by_pgp_key(key.key)
    if owner:
        return owner
    if key.parent:
        return find_key_owner(keys[key.parent], keys, finder)
    return None


def import_keys(keyring):
    outdata = call_gpg(keyring, "--list-sigs")
    keydata = parse_keydata(outdata)

    logger.info("creating or finding %d keys", len(keydata))
    created_ct = updated_ct = 0
    with transaction.atomic():
        finder = UserFinder()
        # we are dependent on parents coming before children; parse_keydata
        # uses an OrderedDict to ensure this is the case.
        for data in list(keydata.values()):
            parent_id = None
            if data.parent:
                parent_data = keydata.get(data.parent, None)
                if parent_data:
                    parent_id = parent_data.db_id
            other = {
                'expires': data.expires,
                'revoked': data.revoked,
                'parent_id': parent_id,
            }
            dkey, created = DeveloperKey.objects.get_or_create(
                    key=data.key, created=data.created, defaults=other)
            data.db_id = dkey.id

            # set or update any additional data we might need to
            needs_save = False
            if created:
                created_ct += 1
            else:
                for k, v in list(other.items()):
                    if getattr(dkey, k) != v:
                        setattr(dkey, k, v)
                        needs_save = True
            if dkey.owner_id is None:
                owner = find_key_owner(data, keydata, finder)
                if owner is not None:
                    dkey.owner = owner
                    needs_save = True
            if needs_save:
                dkey.save()
                updated_ct += 1

    key_ct = DeveloperKey.objects.all().count()
    logger.info("%d total keys in database", key_ct)
    logger.info("created %d, updated %d keys", created_ct, updated_ct)


class SignatureData(object):
    def __init__(self, signer, signee, created):
        self.signer = signer
        self.signee = signee
        self.created = created
        self.expires = None
        self.revoked = None


def parse_sigdata(data):
    nodes = {}
    edges = []
    current_pubkey = None

    # parse all of the output from our successful GPG command
    logger.info("parsing command output")
    for line in data.split('\n'):
        parts = line.split(':')
        if parts[0] == 'pub':
            current_pubkey = parts[4]
            nodes[current_pubkey] = None
        elif parts[0] == 'uid':
            uid = parts[9]
            # only set uid if this is the first one encountered
            if nodes[current_pubkey] is None:
                nodes[current_pubkey] = uid
        elif parts[0] == 'sig':
            signer = parts[4]
            created = get_date(parts[5])
            edge = SignatureData(signer, current_pubkey, created)
            if parts[6]:
                edge.expires = get_date(parts[6])
            edges.append(edge)
        elif parts[0] == 'rev':
            signer = parts[4]
            revoked = get_date(parts[5])
            # revoke any prior edges that match
            matches = [e for e in edges if e.signer == signer
                    and e.signee == current_pubkey]
            for edge in matches:
                edge.revoked = revoked

    return nodes, edges


def import_signatures(keyring):
    outdata = call_gpg(keyring, "--list-sigs")
    nodes, edges = parse_sigdata(outdata)

    # now prune the data down to what we actually want.
    # prune edges not in nodes, remove duplicates, and self-sigs
    pruned_edges = {edge for edge in edges
            if edge.signer in nodes and edge.signer != edge.signee}

    logger.info("creating or finding up to %d signatures", len(pruned_edges))
    created_ct = updated_ct = 0
    with transaction.atomic():
        for edge in pruned_edges:
            sig, created = PGPSignature.objects.get_or_create(
                    signer=edge.signer, signee=edge.signee,
                    created=edge.created, expires=edge.expires,
                    defaults={ 'revoked': edge.revoked })
            if sig.revoked != edge.revoked:
                sig.revoked = edge.revoked
                sig.save()
                updated_ct += 1
            if created:
                created_ct += 1

    sig_ct = PGPSignature.objects.all().count()
    logger.info("%d total signatures in database", sig_ct)
    logger.info("created %d, updated %d signatures", created_ct, updated_ct)

# vim: set ts=4 sw=4 et:

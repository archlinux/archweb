# -*- coding: utf-8 -*-
"""
import_signatures command

Import signatures from a given GPG keyring.

Usage: ./manage.py generate_keyring <keyring_path>
"""

from collections import namedtuple
from datetime import datetime
import logging
import subprocess
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from devel.models import PGPSignature

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(BaseCommand):
    args = "<keyring_path>"
    help = "Import signatures from a given GPG keyring."

    def handle(self, *args, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v == 2:
            logger.level = logging.DEBUG

        if len(args) < 1:
            raise CommandError("keyring_path must be provided")

        import_signatures(args[0])


SignatureData = namedtuple('SignatureData',
        ('signer', 'signee', 'created', 'expires', 'valid'))


def get_date(epoch_string):
    '''Convert a epoch string into a python 'date' object (not datetime).'''
    return datetime.utcfromtimestamp(int(epoch_string)).date()


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
        if parts[0] == 'uid':
            uid = parts[9]
            # only set uid if this is the first one encountered
            if nodes[current_pubkey] is None:
                nodes[current_pubkey] = uid
        if parts[0] == 'sig':
            signer = parts[4]
            created = get_date(parts[5])
            expires = None
            if parts[6]:
                expires = get_date(parts[6])
            valid = parts[1] != '-'
            edge = SignatureData(signer, current_pubkey,
                    created, expires, valid)
            edges.append(edge)

    return nodes, edges


def import_signatures(keyring):
    gpg_cmd = ["gpg", "--no-default-keyring", "--keyring", keyring,
            "--list-sigs", "--with-colons", "--fixed-list-mode"]
    logger.info("running command: %r", gpg_cmd)
    proc = subprocess.Popen(gpg_cmd, stdout=subprocess.PIPE)
    outdata, errdata = proc.communicate()
    if proc.returncode != 0:
        logger.error(errdata)
        raise subprocess.CalledProcessError(proc.returncode, gpg_cmd)

    nodes, edges = parse_sigdata(outdata)

    # now prune the data down to what we actually want.
    # prune edges not in nodes, remove duplicates, and self-sigs
    pruned_edges = set(edge for edge in edges
            if edge.signer in nodes and edge.signer != edge.signee)

    logger.info("creating or finding %d signatures", len(pruned_edges))
    created_ct = updated_ct = 0
    with transaction.commit_on_success():
        for edge in pruned_edges:
            sig, created = PGPSignature.objects.get_or_create(
                    signer=edge.signer, signee=edge.signee,
                    created=edge.created, expires=edge.expires,
                    defaults={ 'valid': edge.valid })
            if sig.valid != edge.valid:
                sig.valid = edge.valid
                sig.save()
                updated_ct = 1
            if created:
                created_ct += 1

    sig_ct = PGPSignature.objects.all().count()
    logger.info("%d total signatures in database", sig_ct)
    logger.info("created %d, updated %d signatures", created_ct, updated_ct)

# vim: set ts=4 sw=4 et:

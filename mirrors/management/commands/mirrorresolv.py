# -*- coding: utf-8 -*-
"""
mirrorresolv command

Poll all mirror URLs and determine whether they have IPv4 and/or IPv6 addresses
available.

Usage: ./manage.py mirrorresolv
"""

from django.core.management.base import NoArgsCommand

import sys
import logging
import socket

from mirrors.models import MirrorUrl

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(NoArgsCommand):
    help = "Runs a check on all active mirror URLs to determine if they are reachable via IPv4 and/or v6."

    def handle_noargs(self, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.WARNING
        elif v == 2:
            logger.level = logging.DEBUG

        return resolve_mirrors()

def resolve_mirrors():
    logger.debug("requesting list of mirror URLs")
    for mirrorurl in MirrorUrl.objects.filter(active=True, mirror__active=True):
        try:
            # save old values, we can skip no-op updates this way
            oldvals = (mirrorurl.has_ipv4, mirrorurl.has_ipv6)
            logger.debug("resolving %3i (%s)", mirrorurl.id, mirrorurl.hostname)
            families = mirrorurl.address_families()
            mirrorurl.has_ipv4 = socket.AF_INET in families
            mirrorurl.has_ipv6 = socket.AF_INET6 in families
            logger.debug("%s: v4: %s v6: %s", mirrorurl.hostname,
                    mirrorurl.has_ipv4, mirrorurl.has_ipv6)
            # now check new values, only update if new != old
            newvals = (mirrorurl.has_ipv4, mirrorurl.has_ipv6)
            if newvals != oldvals:
                logger.debug("values changed for %s", mirrorurl)
                mirrorurl.save(update_fields=('has_ipv4', 'has_ipv6'))
        except socket.error, e:
            logger.warn("error resolving %s: %s", mirrorurl.hostname, e)

# vim: set ts=4 sw=4 et:

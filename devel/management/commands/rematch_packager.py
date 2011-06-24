# -*- coding: utf-8 -*-
"""
rematch_packager command

Match all packages with a packager_str but NULL packager_id to a packager if we
can find one.

Usage: ./manage.py rematch_packager
"""

from django.core.management.base import NoArgsCommand

import sys
import logging

from devel.utils import UserFinder
from main.models import Package

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(NoArgsCommand):
    help = "Runs a check on all active mirror URLs to determine if they are reachable via IPv4 and/or v6."

    def handle_noargs(self, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v == 2:
            logger.level = logging.DEBUG

        return match_packager()

def match_packager():
    finder = UserFinder()
    logger.info("getting all unmatched packages")
    package_count = matched_count = 0
    unknown = set()

    for package in Package.objects.filter(packager__isnull=True):
        logger.debug("package %s, packager string %s",
                package.pkgname, package.packager_str)
        package_count += 1
        user = finder.find(package.packager_str)
        if user:
            package.packager = user
            logger.debug("  found user %s" % user.username)
            package.save()
            matched_count += 1
        else:
            unknown.add(package.packager_str)

    logger.info("%d packages checked, %d newly matched",
            package_count, matched_count)
    logger.debug("unknown packagers:\n%s",
            "\n".join(unknown))

# vim: set ts=4 sw=4 et:

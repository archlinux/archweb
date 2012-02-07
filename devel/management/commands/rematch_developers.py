# -*- coding: utf-8 -*-
"""
rematch_developers command

Match all packages with a packager_str but NULL packager_id to a packager if we
can find one.

Also, match all flag requests with a NULL user_id that have a user_email
matching up to a developer if we can find one.

Usage: ./manage.py rematch_developers
"""

from django.core.management.base import NoArgsCommand
from django.db import transaction

import sys
import logging

from devel.utils import UserFinder
from main.models import Package
from packages.models import FlagRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(NoArgsCommand):
    help = "Match and map objects in database to developer emails"

    def handle_noargs(self, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v == 2:
            logger.level = logging.DEBUG

        finder = UserFinder()
        match_packager(finder)
        match_flagrequest(finder)

@transaction.commit_on_success
def match_packager(finder):
    logger.info("getting all unmatched packages")
    package_count = matched_count = 0
    unknown = set()

    for package in Package.objects.filter(packager__isnull=True):
        if package.packager_str in unknown:
            continue
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

    logger.info("%d packager strings checked, %d newly matched",
            package_count, matched_count)
    logger.debug("unknown packagers:\n%s",
            "\n".join(unknown))


@transaction.commit_on_success
def match_flagrequest(finder):
    logger.info("getting all non-user flag requests")
    req_count = matched_count = 0
    unknown = set()

    for request in FlagRequest.objects.filter(user__isnull=True):
        if request.user_email in unknown:
            continue
        logger.debug("email %s", request.user_email)
        req_count += 1
        user = finder.find_by_email(request.user_email)
        if user:
            request.user = user
            logger.debug("  found user %s" % user.username)
            request.save()
            matched_count += 1
        else:
            unknown.add(request.user_email)

    logger.info("%d request emails checked, %d newly matched",
            req_count, matched_count)

# vim: set ts=4 sw=4 et:

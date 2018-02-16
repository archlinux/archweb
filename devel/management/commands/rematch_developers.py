# -*- coding: utf-8 -*-
"""
rematch_developers command

Match all packages with a packager_str but NULL packager_id to a packager if we
can find one.

Also, match all flag requests with a NULL user_id that have a user_email
matching up to a developer if we can find one.

Usage: ./manage.py rematch_developers
"""

from django.core.management.base import BaseCommand
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

class Command(BaseCommand):
    help = "Match and map objects in database to developer emails"

    def handle(self, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        finder = UserFinder()
        match_packager(finder)
        match_flagrequest(finder)

@transaction.atomic
def match_packager(finder):
    logger.info("getting all unmatched packager strings")
    package_count = matched_count = 0
    mapping = {}

    unmatched = Package.objects.filter(packager__isnull=True).values_list(
            'packager_str', flat=True).order_by().distinct()

    logger.info("%d packager strings retrieved", len(unmatched))
    for packager in unmatched:
        logger.debug("packager string %s", packager)
        user = finder.find(packager)
        if user:
            mapping[packager] = user
            logger.debug("  found user %s", user.username)
            matched_count += 1

    for packager_str, user in list(mapping.items()):
        package_count += Package.objects.filter(packager__isnull=True,
                packager_str=packager_str).update(packager=user)

    logger.info("%d packages updated, %d packager strings matched",
            package_count, matched_count)


@transaction.atomic
def match_flagrequest(finder):
    logger.info("getting all flag request email addresses from unknown users")
    req_count = matched_count = 0
    mapping = {}

    unmatched = FlagRequest.objects.filter(user__isnull=True).values_list(
            'user_email', flat=True).order_by().distinct()

    logger.info("%d email addresses retrieved", len(unmatched))
    for user_email in unmatched:
        logger.debug("email %s", user_email)
        user = finder.find_by_email(user_email)
        if user:
            mapping[user_email] = user
            logger.debug("  found user %s", user.username)
            matched_count += 1

    for user_email, user in list(mapping.items()):
        req_count += FlagRequest.objects.filter(user__isnull=True,
                user_email=user_email).update(user=user)

    logger.info("%d request emails updated, %d emails matched",
            req_count, matched_count)

# vim: set ts=4 sw=4 et:

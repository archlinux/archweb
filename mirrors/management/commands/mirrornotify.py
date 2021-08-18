# -*- coding: utf-8 -*-
"""
mirrornotify command

Notify mirrors admins that:

* The mirror is out of sync, lastsync time > 72 hours
* The mirror is "unreachable" for longer then 24 hours
* The last update file is 72 hours older than the lastupdate file on our master mirror

Usage: ./manage.py mirrornotify
"""

from django.core.management.base import BaseCommand

import sys
import logging

from datetime import datetime, timedelta
from pytz import utc

from mirrors.models import MirrorUrl, MirrorLog

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class Command(BaseCommand):
    help = "TODO."

    def handle(self, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.WARNING
        elif v >= 2:
            logger.level = logging.DEBUG

        return resolve_mirrors()


def resolve_mirrors():
    now = datetime.utcnow().replace(tzinfo=utc)
    issues = []
    logger.debug("checking for mirrors with issues")

    for mirrorurl in MirrorUrl.objects.filter(active=True, mirror__active=True):
        mirrorlog = mirrorurl.logs.last()

        print(mirrorlog.check_time)
        print(now)
        # Mirror has syncing issues for longer then one day
        if mirrorlog.error:
            if mirrorlog.last_sync and mirrorlog.last_sync > now + timedelta(days=1):
                logger.info("mirror: %s, error: '%s' for one day", mirrorurl.url, mirrorlog.error)
                print(mirrorlog.error)
            else:  # TODO: mirror has never synced
                logger.info("mirror: %s, error: '%s' for one day", mirrorurl.url, mirrorlog.error)
                print(mirrorlog.error)

        # Mirror has not synced for 3 days.
        if mirrorlog.last_sync + timedelta(days=3) > now:
            logger.info("mirror: %s, last sync was: '%s'", mirrorurl.url, mirrorlog.last_sync)
            print(mirrorlog.error)


# vim: set ts=4 sw=4 et:

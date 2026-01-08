"""
read_rebuilderd_status command

Import reproducible status of packages, rebuilderd url configured in django
settings.

Usage: ./manage.py read_rebuilderd_status
"""

import logging
import re
from collections import defaultdict

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template import loader

from devel.models import UserProfile
from main.models import Arch, Package, RebuilderdStatus, Repo

EPOCH_REGEX = r'^(\d+):(.+)'

logger = logging.getLogger("command")


class Command(BaseCommand):
    help = "Import reproducible status from rebuilderd."

    def handle(self, *args, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        url = getattr(settings, "REBUILDERD_URL", None)
        if not url:
            logger.error("no rebuilderd_url configured in local_settings.py")

        was_repro = import_rebuilderd_status(url)

        if was_repro:
            send_repro_emails(was_repro)


def send_repro_emails(was_repro):
    template = loader.get_template('devel/email_reproduciblebuilds.txt')
    enabled_users = [prof.user for prof in UserProfile.objects.filter(rebuilderd_updates=True).all()]

    # Group statuses by maintainer
    maintainers_map = defaultdict(list)

    for status in was_repro:
        for maintainer in status.pkg.maintainers:
            if maintainer not in enabled_users:
                continue

            maintainers_map[maintainer.userprofile].append(status.pkg.pkgname)
    for maintainer, pkgs in maintainers_map.items():
        send_mail('Packages which have become not reproducible',
                  template.render({'pkgs': pkgs}),
                  'Arch Website Notification <nobody@archlinux.org>',
                  [maintainer.public_email],
                  fail_silently=True)


def import_rebuilderd_status(url):
    statuses = []
    was_repro = []
    headers = {}

    last_modified = cache.get('rebuilderd:last-modified')
    if last_modified:
        logger.debug('Setting If-Modified-Since header')
        headers = {'If-Modified-Since': last_modified}

    req = requests.get(url, headers=headers)
    if req.status_code == 304:
        logger.debug('The rebuilderd data has not been updated since we last checked it')
        return was_repro

    last_modified = req.headers.get('last-modified')
    if last_modified:
        cache.set('rebuilderd:last-modified', last_modified, 86400)

    data = req.json()

    # Lookup dictionary to reduce SQL queries.
    arches = {arch.name: arch for arch in Arch.objects.all()}
    repos = {repo.name.lower(): repo for repo in Repo.objects.all()}

    for pkg in data:
        arch = arches[pkg['architecture']]
        repository = repos[pkg['suite'].lower()]

        epoch = 0
        pkgname = pkg['name']
        version = pkg['version']
        build_id = pkg['build_id']

        matches = re.search(EPOCH_REGEX, version)
        if matches:
            epoch = matches.group(1)
            version = matches.group(2)

        pkgver, pkgrel = version.rsplit('-', 1)

        dbpkg = Package.objects.filter(pkgname=pkgname, pkgver=pkgver,
                                       pkgrel=pkgrel, epoch=epoch,
                                       repo=repository,
                                       arch=arch).first()
        if not dbpkg:
            continue

        rbstatus = RebuilderdStatus.objects.filter(pkg=dbpkg).first()
        status = RebuilderdStatus.REBUILDERD_API_STATUSES.get(pkg['status'], RebuilderdStatus.UNKNOWN)

        # Existing status
        if rbstatus:
            changed = False

            if rbstatus.build_id != build_id:
                changed = True
                rbstatus.build_id = build_id

            # If status has become BAD, set was_repro
            if rbstatus.status == RebuilderdStatus.GOOD and status == RebuilderdStatus.BAD:
                changed = True
                was_repro.append(rbstatus)
                rbstatus.was_repro = True
                logger.info("package '%s' was good is now bad", pkg['name'])

            if rbstatus.pkgver != pkgver or rbstatus.pkgrel != pkgrel or rbstatus.epoch != epoch:
                changed = True
                logger.info('updating status for package: %s to %s', pkg['name'],
                            RebuilderdStatus.REBUILDERD_STATUSES[status][1])
                rbstatus.epoch = epoch
                rbstatus.pkgver = pkgver
                rbstatus.pkgrel = pkgrel
                rbstatus.status = status
                rbstatus.arch = arch
                rbstatus.repo = repository
            elif rbstatus.status != status:  # Rebuilderd rebuild the same package?
                changed = True
                logger.info('status for package: %s changed to %s', pkg['name'],
                            RebuilderdStatus.REBUILDERD_STATUSES[status][1])
                rbstatus.status = status
                # reset was_repro status as it's unknown
                rbstatus.was_repro = False

            if changed:
                logging.debug('saving updated status for package: %s', pkg['name'])
                rbstatus.save()

        else:  # new package/status
            logger.info('adding status for package: %s', pkg['name'])
            rbstatus = RebuilderdStatus(pkg=dbpkg, status=status, arch=arch, repo=repository,
                                        pkgname=pkgname, epoch=epoch, pkgrel=pkgrel,
                                        pkgver=pkgver)

            if build_id:
                rbstatus.build_id = build_id

            statuses.append(rbstatus)

    if statuses:
        RebuilderdStatus.objects.bulk_create(statuses)

    return was_repro

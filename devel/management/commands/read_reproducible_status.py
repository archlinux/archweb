# -*- coding: utf-8 -*-
"""
read_reproducible_status command

Import reproducible status of packages, rebuilderd url configured in django
settings.

Usage: ./manage.py read_reproducible_status
"""

import logging
import re
import sys

from collections import defaultdict

import requests

from django.core.mail import send_mail
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader

from devel.models import UserProfile
from main.models import Arch, Repo, Package, RebuilderdStatus


EPOCH_REGEX = r'^(\d+):'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


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

        send_repro_emails(was_repro)


def send_repro_emails(was_repro):
    template = loader.get_template('devel/email_reproduciblebuilds.txt')
    enabled_users = [prof.user for prof in UserProfile.objects.filter(rebuilderd_updates=True).all()]

    # Group statusses by maintainer
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

    req = requests.get(url)
    data = req.json()

    for pkg in data:
        arch = Arch.objects.get(name=pkg['architecture'])
        repository = Repo.objects.get(name__iexact=pkg['suite'])

        epoch = 0
        pkgname = pkg['name']
        version = pkg['version']

        matches = re.search(EPOCH_REGEX, version)
        if matches:
            epoch = matches.group(1)

        pkgver, pkgrel = pkg['version'].rsplit('-', 1)

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
            # If status has become BAD, set was_repro
            if rbstatus.status == RebuilderdStatus.GOOD and status == RebuilderdStatus.BAD:
                was_repro.append(rbstatus)
                rbstatus.was_repro = True
                logger.info("package '%s' was good is now bad", pkg['name'])
            else:  # reset status
                rbstatus.was_repro = False

            if rbstatus.pkgver != pkgver or rbstatus.pkgrel != pkgrel or rbstatus.epoch != epoch:
                logger.info('updating status for package: %s to %s', pkg['name'],
                            RebuilderdStatus.REBUILDERD_STATUSES[status][1])
                rbstatus.epoch = epoch
                rbstatus.pkgver = pkgver
                rbstatus.pkgrel = pkgrel
                rbstatus.status = status
                rbstatus.arch = arch
                rbstatus.repo = repository
            elif rbstatus.status != status:  # Rebuilderd rebuild the same package?
                logger.info('status for package: %s changed to %s', pkg['name'],
                            RebuilderdStatus.REBUILDERD_STATUSES[status][1])
                rbstatus.status = status

            # TODO: does django know when a model was really modified?
            rbstatus.save()

        else:  # new package/status
            logger.info('adding status for package: %s', pkg['name'])
            rbstatus = RebuilderdStatus(pkg=dbpkg, status=status, arch=arch, repo=repository,
                                        pkgname=pkgname, epoch=epoch, pkgrel=pkgrel,
                                        pkgver=pkgver)
            statuses.append(rbstatus)

    if statuses:
        RebuilderdStatus.objects.bulk_create(statuses)

    return was_repro

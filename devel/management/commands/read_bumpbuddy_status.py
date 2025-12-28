#!/usr/bin/python


"""
read_bumpbuddy_status

Usage: ./manage.py read_bumpbuddy_status
"""


import logging

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from main.models import Package
from packages.models import FlagRequest

logger = logging.getLogger("command")
logger.setLevel(logging.WARNING)


class Command(BaseCommand):

    def process_package(self, pkgdata):
        pkgbase = pkgdata['pkgbase']
        version = pkgdata['local_version']
        logger.debug("Import new out of date package '%s'", pkgbase)
        print(pkgdata)

        # TODO: testing/staging packages, verify if should be flagged?
        packages = Package.objects.filter(pkgbase=pkgbase)
        flagged_packages = list(packages)

        if len(flagged_packages) == 0:
            logger.warning("no matching packages found for pkgbase='%s', pkgver='%s'", pkgbase, version)
            return


        pkg = packages[0]
        if pkg.flag_date is not None:
            logger.debug("package is already flagged pkgbase='%d'", pkgbase)
            return

        versions = {(pkg.pkgver, pkg.pkgrel, pkg.epoch) for pkg in flagged_packages}
        if len(versions) == 1:
            version = versions.pop()
        else:
            version = ('', '', 0)
        current_time = now()

        flag_request = FlagRequest(created=current_time,
                                   user_email="bumpbuddy@archlinux.org",
                                   message=f"New version {pkgdata['upstream_version']} is available",
                                   ip_address="0.0.0.0",
                                   pkgbase=pkg.pkgbase,
                                   repo=pkg.repo,
                                   pkgver=version[0],
                                   pkgrel=version[1],
                                   epoch=version[2],
                                   num_packages=len(packages))

        return flag_request

    def handle(self, *args, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        url = getattr(settings, "BUMPBUDDY_URL", None)
        headers = {}
        last_modified = cache.get('bumpbuddy:last-modified')
        if last_modified:
            logger.debug('Setting If-Modified-Since header')
            headers = {'If-Modified-Since': last_modified}

        req = requests.get(url, headers)
        if req.status_code == 304:
            logger.debug('The rebuilderd data has not been updated since we last checked it')
            return

        if req.status_code != 200:
            logger.error("Issues retrieving bumpbuddy data: '%s'", req.status_code)
            return

        last_modified = req.headers.get('last-modified')
        if last_modified:
            cache.set('bumpbuddy:last-modified', last_modified, 3600) # cache one hour

        flagged_packages = []
        for pkgdata in req.json().values():
            if not pkgdata['out_of_date']:
                continue

            package = self.process_package(pkgdata)
            if package is not None:
                flagged_packages.append(package)

        # if flagged_packages:
        #     FlagRequest.objects.bulk_create(flagged_packages)

# vim: set ts=4 sw=4 et:

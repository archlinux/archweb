#!/usr/bin/python


"""
read_bumpbuddy_status

Usage: ./manage.py read_bumpbuddy_status
"""


import logging
from urllib.parse import quote as urlquote

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from main.models import Package
from main.utils import gitlab_project_name_to_path
from packages.alpm import AlpmAPI
from packages.models import FlagRequest

logger = logging.getLogger("command")
logger.setLevel(logging.WARNING)


alpm = AlpmAPI()


class Command(BaseCommand):
    def process_package(self, pkgdata):
        pkgbase = pkgdata['pkgbase']
        version = pkgdata['local_version']
        upstream_version = pkgdata['upstream_version']
        logger.debug("Import new out of date package '%s'", pkgbase)

        packages = Package.objects.filter(pkgbase=pkgbase)
        found_packages = list(packages)

        if len(found_packages) == 0:
            logger.error("no matching packages found for pkgbase='%s'", pkgbase)
            return

        # already flagged
        not_flagged_packages = [pkg for pkg in found_packages if pkg.flag_date is None]
        if len(not_flagged_packages) == 0:
            return

        ood_packages = [pkg for pkg in not_flagged_packages if alpm.vercmp(upstream_version, pkg.pkgver) > 0]
        if len(ood_packages) == 0:
            logger.debug("package is not out of date for pkgbase='%s'", pkgbase)
            return

        pkg = ood_packages[0]

        # find a common version if there is one available to store
        versions = {(pkg.pkgver, pkg.pkgrel, pkg.epoch) for pkg in ood_packages}
        if len(versions) == 1:
            version = versions.pop()
        else:
            version = ('', '', 0)

        current_time = now()
        # Compatibility for old json output without issue
        if 'issue' in pkgdata:
            scm_pkgbase = urlquote(gitlab_project_name_to_path(pkgbase))
            issue_url = f"{settings.GITLAB_PACKAGES_REPO}/{scm_pkgbase}/-/issues/{pkgdata['issue']}"
            message = f"New version {pkgdata['upstream_version']} is available: {issue_url}"
        else:
            message = f"New version {pkgdata['upstream_version']} is available."

        for pkg in ood_packages:
            pkg.flag_date = current_time
            pkg.save()

        flag_request = FlagRequest(created=current_time,
                                   user_email="bumpbuddy@archlinux.org",
                                   message=message,
                                   ip_address="0.0.0.0",
                                   pkgbase=pkg.pkgbase,
                                   repo=pkg.repo,
                                   pkgver=version[0],
                                   pkgrel=version[1],
                                   epoch=version[2],
                                   num_packages=len(ood_packages))

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
        assert url is not None, "BUMPBUDDY_URL not configured"

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
            cache.set('bumpbuddy:last-modified', last_modified, 3600)  # cache one hour

        flagged_packages = []
        for pkgdata in req.json().values():
            package = self.process_package(pkgdata)
            if package is not None:
                flagged_packages.append(package)

        if flagged_packages:
            logger.info("Imported %d new out of date packages", len(flagged_packages))
            FlagRequest.objects.bulk_create(flagged_packages)


# vim: set ts=4 sw=4 et:

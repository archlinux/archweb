# -*- coding: utf-8 -*-
"""
populate_signoffs command

Pull the latest commit message from Gitlab for a given package that is
signoff-eligible and does not have an existing comment attached.

Usage: ./manage.py populate_signoffs
"""

import logging
import urllib.parse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from devel.utils import UserFinder
from main.utils import gitlab_project_name_to_path

from ...models import FakeSignoffSpecification, Signoff, SignoffSpecification
from ...utils import get_signoff_groups

logger = logging.getLogger("command")


class Command(BaseCommand):
    help = """Pull the latest commit message from Git for a given package that
is signoff-eligible and does not have an existing comment attached"""

    def handle(self, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        add_signoff_comments()
        cleanup_signoff_comments()


def create_specification(package, log, finder):
    trimmed_message = log['message'].strip()
    required = package.arch.required_signoffs
    spec = SignoffSpecification(pkgbase=package.pkgbase,
                                pkgver=package.pkgver, pkgrel=package.pkgrel,
                                epoch=package.epoch, arch=package.arch, repo=package.repo,
                                comments=trimmed_message, required=required)
    spec.user = finder.find_by_email(log['author'])
    return spec


def get_tag_info(repo, pkgbase, version):
    # Gitlab requires the path to the gitlab repo to be html encoded and
    # project name encoded in a different special way
    pkgrepo = urllib.parse.quote_plus(f'{settings.GITLAB_PACKAGE_REPO}/') + gitlab_project_name_to_path(pkgbase)
    url = f'https://{settings.GITLAB_INSTANCE}/api/v4/projects/{pkgrepo}/repository/tags'

    logger.debug("getting tags for %s (%s) - %s", pkgbase, repo, url)
    r = requests.get(url)
    if r.status_code != 200:
        # https://gitlab.archlinux.org/api/v4/projects/bot-test%2fpackages%2ftransmission/repository/tags
        logger.error("error getting Git tags for %s (%s)", pkgbase, repo)
        return None

    tags = r.json()

    # filter out unrelated tags
    tags = [tag for tag in tags if tag["name"] == version]

    if len(tags) == 0:
        logger.error("No tags found for pkgbase %s (%s) version %s", pkgbase, repo, version)
        return None

    tag = tags[0]
    log = {
        'message': tag['commit']['message'],
        'author': tag['commit']['committer_email'],
    }

    return log


def add_signoff_comments():
    logger.info("getting all signoff groups")
    groups = get_signoff_groups()
    logger.info("%d signoff groups found", len(groups))

    finder = UserFinder()

    for group in groups:
        if not group.default_spec:
            continue

        log = get_tag_info(group.repo, group.pkgbase, group.version)
        if log is None:
            continue

        try:
            logger.info("creating spec with Git commit message for %s", group.pkgbase)
            spec = create_specification(group.packages[0], log, finder)
            spec.save()
        except: # noqa
            logger.exception("error getting Git commits for %s", group.pkgbase)


def cleanup_signoff_comments():
    logger.info("getting all signoff groups")
    groups = get_signoff_groups()

    id_signoffs = [signoff.id for g in groups for signoff in g.signoffs]
    logger.info("Keeping %s signoffs", len(id_signoffs))
    # FakeSignoffSpecification's have no id
    id_signoffspecs = [g.specification.id for g in groups if not isinstance(g.specification,
                                                                            FakeSignoffSpecification)]
    logger.info("Keeping %s signoffspecifications", len(id_signoffspecs))

    Signoff.objects.exclude(id__in=id_signoffs).delete()
    SignoffSpecification.objects.exclude(id__in=id_signoffspecs).delete()


# vim: set ts=4 sw=4 et:

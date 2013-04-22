# -*- coding: utf-8 -*-
"""
populate_signoffs command

Pull the latest commit message from SVN for a given package that is
signoff-eligible and does not have an existing comment attached.

Usage: ./manage.py populate_signoffs
"""

from datetime import datetime
import logging
import subprocess
import sys
from xml.etree.ElementTree import XML

from django.conf import settings
from django.core.management.base import NoArgsCommand

from ...models import SignoffSpecification
from ...utils import get_signoff_groups
from devel.utils import UserFinder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(NoArgsCommand):
    help = """Pull the latest commit message from SVN for a given package that
is signoff-eligible and does not have an existing comment attached"""

    def handle_noargs(self, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v == 2:
            logger.level = logging.DEBUG

        return add_signoff_comments()

def svn_log(pkgbase, repo):
    '''Retrieve the most recent SVN log entry for the given pkgbase and
    repository. The configured setting SVN_BASE_URL is used along with the
    svn_root for each repository to form the correct URL.'''
    path = '%s%s/%s/trunk/' % (settings.SVN_BASE_URL, repo.svn_root, pkgbase)
    cmd = ['svn', 'log', '--limit=1', '--xml', path]
    log_data = subprocess.check_output(cmd)
    # the XML format is very very simple, especially with only one revision
    xml = XML(log_data)
    revision = int(xml.find('logentry').get('revision'))
    date = datetime.strptime(xml.findtext('logentry/date'),
            '%Y-%m-%dT%H:%M:%S.%fZ')
    return {
        'revision': revision,
        'date': date,
        'author': xml.findtext('logentry/author'),
        'message': xml.findtext('logentry/msg'),
    }

def cached_svn_log(pkgbase, repo):
    '''Retrieve the cached version of the SVN log if possible, else delegate to
    svn_log() to do the work and cache the result.'''
    key = (pkgbase, repo)
    if key in cached_svn_log.cache:
        return cached_svn_log.cache[key]
    log = svn_log(pkgbase, repo)
    cached_svn_log.cache[key] = log
    return log
cached_svn_log.cache = {}

def create_specification(package, log, finder):
    trimmed_message = log['message'].strip()
    required = package.arch.required_signoffs
    spec = SignoffSpecification(pkgbase=package.pkgbase,
            pkgver=package.pkgver, pkgrel=package.pkgrel,
            epoch=package.epoch, arch=package.arch, repo=package.repo,
            comments=trimmed_message, required=required)
    spec.user = finder.find_by_username(log['author'])
    return spec

def add_signoff_comments():
    logger.info("getting all signoff groups")
    groups = get_signoff_groups()
    logger.info("%d signoff groups found", len(groups))

    finder = UserFinder()

    for group in groups:
        if not group.default_spec:
            continue

        logger.debug("getting SVN log for %s (%s)", group.pkgbase, group.repo)
        log = cached_svn_log(group.pkgbase, group.repo)
        logger.info("creating spec with SVN message for %s", group.pkgbase)
        spec = create_specification(group.packages[0], log, finder)
        spec.save()

# vim: set ts=4 sw=4 et:

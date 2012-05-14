# -*- coding: utf-8 -*-
"""
mirrorcheck command

Poll every active mirror URL we have in the database, grab the 'lastsync' file,
and record details about how long it took and how up to date the mirror is. If
we encounter errors, record those as well.

Usage: ./manage.py mirrorcheck
"""

from collections import deque
from datetime import datetime
import logging
import os
from optparse import make_option
from pytz import utc
import re
import socket
import subprocess
import sys
import time
import tempfile
from threading import Thread
import types
from Queue import Queue, Empty
import urllib2

from django.core.management.base import NoArgsCommand
from django.db import transaction

from main.utils import utc_now
from mirrors.models import MirrorUrl, MirrorLog

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('-t', '--timeout', dest='timeout', default='10',
            help='Timeout value for connecting to URL'),
    )
    help = "Runs a check on all known mirror URLs to determine their up-to-date status."

    def handle_noargs(self, **options):
        v = int(options.get('verbosity', 0))
        timeout = int(options.get('timeout', 10))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.WARNING
        elif v == 2:
            logger.level = logging.DEBUG

        urls = MirrorUrl.objects.select_related('protocol').filter(
                mirror__active=True, mirror__public=True)

        pool = MirrorCheckPool(urls, timeout)
        pool.run()
        return 0


def parse_lastsync(log, data):
    '''lastsync file should be an epoch value created by us.'''
    try:
        parsed_time = datetime.utcfromtimestamp(int(data))
        log.last_sync = parsed_time.replace(tzinfo=utc)
    except ValueError:
        # it is bad news to try logging the lastsync value;
        # sometimes we get a crazy-encoded web page.
        # if we couldn't parse a time, this is a failure.
        log.last_sync = None
        log.error = "Could not parse time from lastsync"
        log.is_success = False


def check_mirror_url(mirror_url, timeout):
    url = mirror_url.url + 'lastsync'
    logger.info("checking URL %s", url)
    log = MirrorLog(url=mirror_url, check_time=utc_now())
    headers = {'User-Agent': 'archweb/1.0'}
    req = urllib2.Request(url, None, headers)
    try:
        start = time.time()
        result = urllib2.urlopen(req, timeout=timeout)
        data = result.read()
        result.close()
        end = time.time()
        parse_lastsync(log, data)
        log.duration = end - start
        logger.debug("success: %s, %.2f", url, log.duration)
    except urllib2.HTTPError as e:
        if e.code == 404:
            # we have a duration, just not a success
            end = time.time()
            log.duration = end - start
        log.is_success = False
        log.error = str(e)
        logger.debug("failed: %s, %s", url, log.error)
    except urllib2.URLError as e:
        log.is_success = False
        log.error = e.reason
        if isinstance(e.reason, types.StringTypes) and \
                re.search(r'550.*No such file', e.reason):
            # similar to 404 case above, still record duration
            end = time.time()
            log.duration = end - start
        if isinstance(e.reason, socket.timeout):
            log.error = "Connection timed out."
        elif isinstance(e.reason, socket.error):
            log.error = e.reason.args[1]
        logger.debug("failed: %s, %s", url, log.error)
    except socket.timeout as e:
        log.is_success = False
        log.error = "Connection timed out."
        logger.debug("failed: %s, %s", url, log.error)
    except socket.error as e:
        log.is_success = False
        log.error = str(e)
        logger.debug("failed: %s, %s", url, log.error)

    return log


def check_rsync_url(mirror_url, timeout):
    url = mirror_url.url + 'lastsync'
    logger.info("checking URL %s", url)
    log = MirrorLog(url=mirror_url, check_time=utc_now())

    tempdir = tempfile.mkdtemp()
    lastsync_path = os.path.join(tempdir, 'lastsync')
    rsync_cmd = ["rsync", "--quiet", "--contimeout=%d" % timeout,
            "--timeout=%d" % timeout, url, lastsync_path]
    try:
        with open(os.devnull, 'w') as devnull:
            proc = subprocess.Popen(rsync_cmd, stdout=devnull,
                    stderr=subprocess.PIPE)
            start = time.time()
            _, errdata = proc.communicate()
            end = time.time()
        log.duration = end - start
        if proc.returncode != 0:
            logger.debug("error: %s, %s", url, errdata)
            log.is_success = False
            log.error = errdata.strip()
            # look at rsync error code- if we had a command error or timed out,
            # don't record a duration as it is misleading
            if proc.returncode in (1, 30, 35):
                log.duration = None
        else:
            logger.debug("success: %s, %.2f", url, log.duration)
            with open(lastsync_path, 'r') as lastsync:
                parse_lastsync(log, lastsync.read())
    finally:
        if os.path.exists(lastsync_path):
            os.unlink(lastsync_path)
        os.rmdir(tempdir)

    return log


def mirror_url_worker(work, output, timeout):
    while True:
        try:
            url = work.get(block=False)
            try:
                if url.protocol.protocol == 'rsync':
                    log = check_rsync_url(url, timeout)
                else:
                    log = check_mirror_url(url, timeout)
                output.append(log)
            finally:
                work.task_done()
        except Empty:
            return 0


class MirrorCheckPool(object):
    def __init__(self, urls, timeout=10, num_threads=10):
        self.tasks = Queue()
        self.logs = deque()
        for i in list(urls):
            self.tasks.put(i)
        self.threads = []
        for i in range(num_threads):
            thread = Thread(target=mirror_url_worker,
                    args=(self.tasks, self.logs, timeout))
            thread.daemon = True
            self.threads.append(thread)

    @transaction.commit_on_success
    def run(self):
        logger.debug("starting threads")
        for thread in self.threads:
            thread.start()
        logger.debug("joining on all threads")
        self.tasks.join()
        logger.debug("processing %d log entries", len(self.logs))
        MirrorLog.objects.bulk_create(self.logs)
        logger.debug("log entries saved")

# vim: set ts=4 sw=4 et:

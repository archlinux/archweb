# -*- coding: utf-8 -*-
"""
mirrorcheck command

Poll every active mirror URL we have in the database, grab the 'lastsync' file,
and record details about how long it took and how up to date the mirror is. If
we encounter errors, record those as well.

Usage: ./manage.py mirrorcheck
"""

from django.core.management.base import NoArgsCommand
from django.db import transaction

from collections import deque
from datetime import datetime
import logging
import re
import socket
import sys
import time
from threading import Thread
import types
from pytz import utc
from Queue import Queue, Empty
import urllib2

from main.utils import utc_now
from mirrors.models import MirrorUrl, MirrorLog

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(NoArgsCommand):
    help = "Runs a check on all known mirror URLs to determine their up-to-date status."

    def handle_noargs(self, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.WARNING
        elif v == 2:
            logger.level = logging.DEBUG

        return check_current_mirrors()

def check_mirror_url(mirror_url):
    url = mirror_url.url + 'lastsync'
    logger.info("checking URL %s", url)
    log = MirrorLog(url=mirror_url, check_time=utc_now())
    try:
        start = time.time()
        result = urllib2.urlopen(url, timeout=10)
        data = result.read()
        result.close()
        end = time.time()
        # lastsync should be an epoch value created by us
        parsed_time = None
        try:
            parsed_time = datetime.utcfromtimestamp(int(data))
            parsed_time = parsed_time.replace(tzinfo=utc)
        except ValueError:
            # it is bad news to try logging the lastsync value;
            # sometimes we get a crazy-encoded web page.
            pass

        log.last_sync = parsed_time
        # if we couldn't parse a time, this is a failure
        if parsed_time is None:
            log.error = "Could not parse time from lastsync"
            log.is_success = False
        log.duration = end - start
        logger.debug("success: %s, %.2f", url, log.duration)
    except urllib2.HTTPError, e:
        if e.code == 404:
            # we have a duration, just not a success
            end = time.time()
            log.duration = end - start
        log.is_success = False
        log.error = str(e)
        logger.debug("failed: %s, %s", url, log.error)
    except urllib2.URLError, e:
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
    except socket.timeout, e:
        log.is_success = False
        log.error = "Connection timed out."
        logger.debug("failed: %s, %s", url, log.error)

    return log

def mirror_url_worker(work, output):
    while True:
        try:
            item = work.get(block=False)
            try:
                log = check_mirror_url(item)
                output.append(log)
            finally:
                work.task_done()
        except Empty:
            return 0

class MirrorCheckPool(object):
    def __init__(self, work, num_threads=10):
        self.tasks = Queue()
        self.logs = deque()
        for i in list(work):
            self.tasks.put(i)
        self.threads = []
        for i in range(num_threads):
            thread = Thread(target=mirror_url_worker,
                    args=(self.tasks, self.logs))
            thread.daemon = True
            self.threads.append(thread)

    @transaction.commit_on_success
    def run(self):
        logger.debug("starting threads")
        for thread in self.threads:
            thread.start()
        logger.debug("joining on all threads")
        self.tasks.join()
        logger.debug("processing log entries")
        MirrorLog.objects.bulk_create(self.logs)
        logger.debug("log entries saved")

def check_current_mirrors():
    urls = MirrorUrl.objects.filter(
            protocol__is_download=True,
            mirror__active=True, mirror__public=True)

    pool = MirrorCheckPool(urls)
    pool.run()
    return 0

# For lack of a better place to put it, here is a query to get latest check
# result joined with mirror details:
# SELECT mu.*, m.*, ml.* FROM mirrors_mirrorurl mu JOIN mirrors_mirror m ON mu.mirror_id = m.id JOIN mirrors_mirrorlog ml ON mu.id = ml.url_id LEFT JOIN mirrors_mirrorlog ml2 ON ml.url_id = ml2.url_id AND ml.id < ml2.id WHERE ml2.id IS NULL AND m.active = 1 AND m.public = 1;

# vim: set ts=4 sw=4 et:

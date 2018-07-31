# -*- coding: utf-8 -*-
"""
mirrorcheck command

Poll every active mirror URL we have in the database, grab the 'lastsync' file,
and record details about how long it took and how up to date the mirror is. If
we encounter errors, record those as well.

Usage: ./manage.py mirrorcheck
"""

from collections import deque
from datetime import datetime, timedelta
from http.client import HTTPException
import logging
import os
from pytz import utc
import re
import socket
import ssl
import subprocess
import sys
import time
import tempfile
from threading import Thread
import types
from queue import Queue, Empty
import urllib

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils.timezone import now

from mirrors.models import MirrorUrl, MirrorLog, CheckLocation


logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class Command(BaseCommand):
    help = "Runs a check on all known mirror URLs to determine their up-to-date status."

    def add_arguments(self, parser):
        parser.add_argument('-t',
                            '--timeout',
                            dest='timeout',
                            type=float,
                            default=10.0,
                            help='Timeout value for connecting to URL')
        parser.add_argument('-l',
                            '--location',
                            dest='location',
                            type=int,
                            help='ID of CheckLocation object to use for this run')

    def handle(self, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.WARNING
        elif v >= 2:
            logger.level = logging.DEBUG

        timeout = options.get('timeout')

        urls = MirrorUrl.objects.select_related('protocol').filter(
                active=True, mirror__active=True, mirror__public=True)

        location = options.get('location', None)
        if location:
            location = CheckLocation.objects.get(id=location)
            family = location.family
            monkeypatch_getaddrinfo(family)
            if family == socket.AF_INET6:
                urls = urls.filter(has_ipv6=True)
            elif family == socket.AF_INET:
                urls = urls.filter(has_ipv4=True)

        pool = MirrorCheckPool(urls, location, timeout)
        pool.run()
        pool.cleanup()
        return 0


def monkeypatch_getaddrinfo(force_family=socket.AF_INET):
    '''Force the Python socket module to connect over the designated family;
    e.g. socket.AF_INET or socket.AF_INET6.'''
    orig = socket.getaddrinfo

    def wrapper(host, port, family=0, socktype=0, proto=0, flags=0):
        return orig(host, port, force_family, socktype, proto, flags)

    socket.getaddrinfo = wrapper


def parse_lastsync(log, data):
    '''lastsync file should be an epoch value created by us.'''
    try:
        parsed_time = datetime.utcfromtimestamp(int(data))
        log.last_sync = parsed_time.replace(tzinfo=utc)
    except (TypeError, ValueError):
        # it is bad news to try logging the lastsync value;
        # sometimes we get a crazy-encoded web page.
        # if we couldn't parse a time, this is a failure.
        log.last_sync = None
        log.error = "Could not parse time from lastsync"
        log.is_success = False


def check_mirror_url(mirror_url, location, timeout):
    url = mirror_url.url + 'lastsync'
    logger.info("checking URL %s", url)
    log = MirrorLog(url=mirror_url, check_time=now(), location=location)
    headers = {'User-Agent': 'archweb/1.0'}
    req = urllib.request.Request(url, None, headers)
    start = time.time()
    try:
        result = urllib.request.urlopen(req, timeout=timeout)
        data = result.read()
        result.close()
        end = time.time()
        parse_lastsync(log, data)
        log.duration = end - start
        logger.debug("success: %s, %.2f", url, log.duration)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # we have a duration, just not a success
            end = time.time()
            log.duration = end - start
        log.is_success = False
        log.error = str(e)
        logger.debug("failed: %s, %s", url, log.error)
    except urllib.error.URLError as e:
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
            log.error = e.reason.args[-1]
        logger.debug("failed: %s, %s", url, log.error)
    except HTTPException:
        # e.g., BadStatusLine
        log.is_success = False
        log.error = "Exception in processing HTTP request."
        logger.debug("failed: %s, %s", url, log.error)
    except ssl.CertificateError as e:
        log.is_success = False
        log.error = str(e)
        logger.debug("failed: %s, %s", url, log.error)
    except socket.timeout:
        log.is_success = False
        log.error = "Connection timed out."
        logger.debug("failed: %s, %s", url, log.error)
    except socket.error as e:
        log.is_success = False
        log.error = str(e)
        logger.debug("failed: %s, %s", url, log.error)

    return log


def check_rsync_url(mirror_url, location, timeout):
    url = mirror_url.url + 'lastsync'
    logger.info("checking URL %s", url)
    log = MirrorLog(url=mirror_url, check_time=now(), location=location)

    tempdir = tempfile.mkdtemp()
    ipopt = ''
    if location:
        if location.family == socket.AF_INET6:
            ipopt = '--ipv6'
        elif location.family == socket.AF_INET:
            ipopt = '--ipv4'
    lastsync_path = os.path.join(tempdir, 'lastsync')
    rsync_cmd = ["rsync", "--quiet", "--contimeout=%d" % timeout,
            "--timeout=%d" % timeout]
    if ipopt:
        rsync_cmd.append(ipopt)
    rsync_cmd.append(url)
    rsync_cmd.append(lastsync_path)
    try:
        with open(os.devnull, 'w') as devnull:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("rsync cmd: %s", ' '.join(rsync_cmd))
            start = time.time()
            proc = subprocess.Popen(rsync_cmd, stdout=devnull,
                    stderr=subprocess.PIPE)
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
            if os.path.exists(lastsync_path):
                with open(lastsync_path, 'r') as lastsync:
                    parse_lastsync(log, lastsync.read())
            else:
                parse_lastsync(log, None)
    finally:
        if os.path.exists(lastsync_path):
            os.unlink(lastsync_path)
        os.rmdir(tempdir)

    return log


def mirror_url_worker(work, output, location, timeout):
    while True:
        try:
            url = work.get(block=False)
            try:
                if url.protocol.protocol == 'rsync':
                    log = check_rsync_url(url, location, timeout)
                elif (url.protocol.protocol == 'ftp' and location and
                        location.family == socket.AF_INET6):
                    # IPv6 + FTP don't work; skip checking completely
                    log = None
                else:
                    log = check_mirror_url(url, location, timeout)
                if log:
                    output.append(log)
            finally:
                work.task_done()
        except Empty:
            return 0


class MirrorCheckPool(object):
    def __init__(self, urls, location, timeout=10, num_threads=10):
        self.tasks = Queue()
        self.logs = deque()
        for url in urls:
            self.tasks.put(url)
        self.threads = []
        for _ in range(num_threads):
            thread = Thread(target=mirror_url_worker,
                    args=(self.tasks, self.logs, location, timeout))
            thread.daemon = True
            self.threads.append(thread)

    @transaction.atomic
    def run(self):
        logger.debug("starting threads")
        for thread in self.threads:
            thread.start()
        logger.debug("joining on all threads")
        self.tasks.join()
        logger.debug("processing %d log entries", len(self.logs))
        MirrorLog.objects.bulk_create(self.logs)
        logger.debug("log entries saved")

    def cleanup(self):
        days = getattr(settings, 'MIRRORLOG_RETENTION_PERIOD', 365)
        removal_date = now() - timedelta(days=days)
        logger.info("cleaning up older MirrorLog objects then %s", removal_date.strftime('%Y-%m-%d'))
        MirrorLog.objects.filter(check_time__lt=removal_date).delete()
        logger.info('Finished cleaning up old MirrorLog objects')

# vim: set ts=4 sw=4 et:

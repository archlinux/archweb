# -*- coding: utf-8 -*-
"""
reporead_inotify command

Watches repo.files.tar.gz files for updates and parses them after a short delay
in order to catch all updates in a single bulk update.

Usage: ./manage.py reporead_inotify [path_template]

Where 'path_template' is an optional path_template for finding the
repo.files.tar.gz files. The form is '/srv/ftp/%(repo)s/os/%(arch)s/', which is
also the default template if none is specified. While 'repo' is not required to
be present in the path_template, note that 'arch' is so reporead can function
correctly.
"""

import logging
import multiprocessing
import os
import pyinotify
import sys
import threading
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from main.models import Arch, Repo
from .reporead import read_repo

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class Command(BaseCommand):
    help = "Watch database files and run an update when necessary."
    args = "[path_template]"

    def handle(self, path_template=None, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        if not path_template:
            path_template = '/srv/ftp/%(repo)s/os/%(arch)s/'
        self.path_template = path_template

        notifier = self.setup_notifier()
        # this thread is done using the database; all future access is done in
        # the spawned read_repo() processes, so close the otherwise completely
        # idle connection.
        connection.close()

        logger.info('Entering notifier loop')
        notifier.loop()

        logger.info('Cancelling remaining threads...')
        for thread in threading.enumerate():
            if hasattr(thread, 'cancel'):
                thread.cancel()

    @transaction.atomic
    def setup_notifier(self):
        '''Set up and configure the inotify machinery and logic.
        This takes the provided or default path_template and builds a list of
        directories we need to watch for database updates. It then validates
        and passes these on to the various pyinotify pieces as necessary and
        finally builds and returns a notifier object.'''
        with transaction.atomic():
            arches = Arch.objects.filter(agnostic=False)
            repos = Repo.objects.all()

        arch_path_map = {arch: None for arch in arches}
        all_paths = set()
        total_paths = 0
        for arch in arches:
            combos = ({'repo': repo.name.lower(), 'arch': arch.name}
                      for repo in repos)
            # take a python format string and generate all unique combinations
            # of directories from it; using set() ensures we filter it down
            paths = {self.path_template % values for values in combos}
            total_paths += len(paths)
            all_paths |= paths
            arch_path_map[arch] = paths

        logger.info('Watching %d total paths', total_paths)
        logger.debug(all_paths)

        # sanity check- basically ensure every path we created from the
        # template mapped to only one architecture
        if total_paths != len(all_paths):
            raise CommandError('path template did not uniquely '
                               'determine architecture for each file')

        # A proper atomic replacement of the database as done by rsync is type
        # IN_MOVED_TO. repo-add/remove will finish with a IN_CLOSE_WRITE.
        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO

        manager = pyinotify.WatchManager()
        for name in all_paths:
            manager.add_watch(name, mask)

        handler = EventHandler(arch_paths=arch_path_map)
        return pyinotify.Notifier(manager, handler)


class Database(object):
    '''A object representing a pacman database on the filesystem. It stores
    various bits of metadata and state representing the file path, when we last
    updated, how long our delay is before performing the update, whether we are
    updating now, etc.'''
    def __init__(self, arch, path, delay=60.0, nice=3):
        self.arch = arch
        self.path = path
        self.delay = delay
        self.nice = nice
        self.mtime = None
        self.last_import = None
        self.update_thread = None
        self.updating = False
        self.run_again = False
        self.lock = threading.Lock()

    def _start_update_countdown(self):
        self.update_thread = threading.Timer(self.delay, self.update)
        logger.info('Starting %.1f second countdown to update %s',
                    self.delay, self.path)
        self.update_thread.start()

    def queue_for_update(self, mtime):
        logger.debug('Queueing database %s...', self.path)
        with self.lock:
            self.mtime = mtime
            if self.updating:
                # store the fact that we will need to run it again
                self.run_again = True
                return
            if self.update_thread:
                self.update_thread.cancel()
                self.update_thread = None
            self._start_update_countdown()

    def update(self):
        logger.debug('Updating database %s...', self.path)
        with self.lock:
            self.last_import = time.time()
            self.updating = True

        try:
            # invoke reporead's primary method. we do this in a separate
            # process for memory conservation purposes; these processes grow
            # rather large so it is best to free up the memory ASAP.
            def run():
                if self.nice != 0:
                    os.nice(self.nice)
                read_repo(self.arch, self.path, {})

            process = multiprocessing.Process(target=run)
            process.start()
            process.join()
        finally:
            logger.debug('Done updating database %s.', self.path)
            with self.lock:
                self.update_thread = None
                self.updating = False
                if self.run_again:
                    self.run_again = False
                    self._start_update_countdown()


class EventHandler(pyinotify.ProcessEvent):
    '''Our main event handler which listens for database change events. Because
    we are watching the whole directory, we filter down and only look at those
    events dealing with files databases.'''

    def my_init(self, **kwargs):
        self.databases = {}
        self.arch_lookup = {}

        # we really want a single path to arch mapping, so massage the data
        arch_paths = kwargs['arch_paths']
        for arch, paths in list(arch_paths.items()):
            self.arch_lookup.update((path.rstrip('/'), arch) for path in paths)

    def process_default(self, event):
        '''Primary event processing function which kicks off reporead timer
        threads if a files database was updated.'''
        name = event.name
        if not name:
            return
        # screen to only the files we care about, skipping temp files
        if name.endswith('.files.tar.gz') and not name.startswith('.'):
            path = event.pathname
            stat = os.stat(path)
            database = self.databases.get(path, None)
            if database is None:
                arch = self.arch_lookup.get(event.path, None)
                if arch is None:
                    logger.warning(
                            'Could not determine arch for %s, skipping update',
                            path)
                    return
                database = Database(arch, path)
                self.databases[path] = database
            database.queue_for_update(stat.st_mtime)


# vim: set ts=4 sw=4 et:

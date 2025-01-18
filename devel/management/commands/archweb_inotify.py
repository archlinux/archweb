import logging
import multiprocessing
import os
import threading
import time

import pyinotify
from django.db.utils import OperationalError

logger = logging.getLogger("command")
logger.setLevel(logging.WARNING)


class Database(object):
    '''A object representing a pacman database on the filesystem. It stores
    various bits of metadata and state representing the file path, when we last
    updated, how long our delay is before performing the update, whether we are
    updating now, etc.'''
    def __init__(self, arch, path, callback_func, delay=60.0, nice=3, retry_limit=5):
        self.arch = arch
        self.path = path
        self.delay = delay
        self.nice = nice
        self.retry_limit = retry_limit
        self.mtime = None
        self.last_import = None
        self.update_thread = None
        self.updating = False
        self.run_again = False
        self.lock = threading.Lock()
        self.callback_func = callback_func

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
            # A retry mechanism exists for when reporead_inotify runs on a different machine.
            def run():
                retry = True
                retry_count = 0
                if self.nice != 0:
                    os.nice(self.nice)
                while retry and retry_count < self.retry_limit:
                    try:
                        self.callback_func(self.arch, self.path, {})
                        retry = False
                    except OperationalError as exc:
                        retry_count += 1
                        logger.error('Unable to update database \'%s\', retrying=%d',
                                     self.path, retry_count, exc_info=exc)
                        time.sleep(5)

                if retry_count == self.retry_limit:
                    logger.error('Unable to update database, exceeded maximum retries')

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

    def my_init(self, filename_suffix, callback_func, **kwargs):
        self.databases = {}
        self.arch_lookup = {}

        self.filename_suffix = filename_suffix
        self.callback_func = callback_func

        # we really want a single path to arch mapping, so massage the data
        arch_paths = kwargs['arch_paths']
        for arch, paths in arch_paths.items():
            self.arch_lookup.update((path.rstrip('/'), arch) for path in paths)

    def process_default(self, event):
        '''Primary event processing function which kicks off reporead timer
        threads if a files database was updated.'''
        name = event.name
        if not name:
            return
        # screen to only the files we care about, skipping temp files
        if name.endswith(self.filename_suffix) and not name.startswith('.'):
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
                database = Database(arch, path, self.callback_func)
                self.databases[path] = database
            database.queue_for_update(stat.st_mtime)


# vim: set ts=4 sw=4 et:

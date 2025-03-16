import logging
import threading

import pyinotify
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from main.models import Arch, Repo

from .archweb_inotify import EventHandler
from .readlinks import read_links

logger = logging.getLogger("command")


def wrapper_read_links(arch, filepath, obj):
    read_links(filepath)


class Command(BaseCommand):
    help = "Watch links files and run an update when necessary."
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

        arch_path_map = dict.fromkeys(arches)
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

        handler = EventHandler(arch_paths=arch_path_map,
                               filename_suffix='.links.tar.gz',
                               callback_func=wrapper_read_links)
        return pyinotify.Notifier(manager, handler)


# vim: set ts=4 sw=4 et:

import logging

from django.core import management


class BaseCommand(management.base.BaseCommand):
    stealth_options = ('logger',)
    __verbosity_to_level = [ logging.WARNING, logging.INFO, logging.DEBUG ]

    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger('archweb.command')

    def execute(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        level = self.__verbosity_to_loglevel(verbosity)
        self.logger.setLevel(level)

        if options.get('logger'):
            self.logger = options['logger']

        super(BaseCommand, self).execute(*args, **options)

    @classmethod
    def __verbosity_to_loglevel(cls, verbosity):
        if verbosity < 0:
            return logging.WARNING
        if verbosity >= len(cls.__verbosity_to_level):
            return logging.DEBUG
        return cls.__verbosity_to_level[verbosity]

# -*- coding: utf-8 -*-
"""
retire_user

Retire a user by de-activing the account and moving the user to the retired
group.

Usage ./manage.py retire_user user
"""

import logging
import sys

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError

from devel.models import UserProfile


logging.basicConfig(
    level=logging.WARNING,
    format=u'%(asctime)s -> %(levelname)s: %(message)s',
    datefmt=u'%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

MAPPING = {
    'Developers': 'Retired Developers',
    'Trusted Users': 'Retired Trusted Users',
    'Support Staff': 'Retired Support Staff',
}


class Command(BaseCommand):
    help = "Retires a user by deactivating the user and moving the group membership to retired groups."
    missing_args_message = 'missing argument user.'

    def add_arguments(self, parser):
        parser.add_argument('user', type=str)

    def handle(self, *args, **options):
        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(u"Failed to find User '{}'".format(options['user']))

        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            raise CommandError(u"Failed to find UserProfile")

        # Set user inactive
        user.is_active = False

        # Clear allowed repos
        profile.allowed_repos.clear()

        # Move Groups to Retired.
        del_groups = list(user.groups.filter(name__in=MAPPING.keys()))
        add_groups = [Group.objects.get(name=MAPPING.get(group.name)) for group in del_groups]
        user.groups.remove(*del_groups)
        user.groups.add(*add_groups)
        user.save()

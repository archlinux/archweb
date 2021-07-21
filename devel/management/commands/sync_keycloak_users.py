#!/usr/bin/python

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from devel.models import UserProfile
from devel.auth.constants import OIDC_GROUP_MAPPING, OIDC_DEVOPS_GROUP
from main.models import Repo

import logging
import sys

from keycloak import KeycloakAdmin
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


def update_keycloak_users(url, client_id, client_secret, realm_name):
    logger.debug("Syncing archweb SSO users to Keycloak groups")

    kc_admin = KeycloakAdmin(server_url=url,
                             realm_name=realm_name,
                             client_id=client_id,
                             client_secret_key=client_secret,
                             username=client_id,
                             password=client_secret)

    for userprofile in UserProfile.objects.filter(sso_accountid__isnull=False).select_related('user'):
        is_devops = False
        changed = False

        print(userprofile)
        user = userprofile.user
        accountid = userprofile.sso_accountid
        archweb_group_names = []
        for group in kc_admin.get_user_groups(accountid):
            archweb_groupname = OIDC_GROUP_MAPPING.get(group['path'])
            # Handle DevOps permissions
            if group['path'] == OIDC_DEVOPS_GROUP:
                is_devops = True

            if archweb_groupname:
                archweb_group_names.append(archweb_groupname)

        current_groups = user.groups.values_list('name', flat=True)
        if set(current_groups) != set(archweb_group_names):
            logger.info("User: '%s' has different groups in archweb, set groups from keycloak", user.username)
            groups = [Group.objects.get(name=grp) for grp in archweb_group_names]
            user.groups.clear()
            user.groups.set(groups)
            changed = True

        # Remove django admin permissions from ex-DevOps
        if not is_devops and user.is_staff or user.is_superuser:
            print('not devops')
            user.is_staff = False
            user.is_superuser = False
            changed = True

        if changed:
            user.save()
            userprofile.save()


class Command(BaseCommand):
    help = "Sync Keycloak users to Archweb."

    def handle(self, *args, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

    keycloak_url = getattr(settings, 'KEYCLOAK_SERVICE_ACCOUNT_ENDPOINT', None)
    client_id = getattr(settings, 'KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID', None)
    client_secret = getattr(settings, 'KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET', None)
    realm = getattr(settings, 'KEYCLOAK_SERVICE_ACCOUNT_REALM', None)
    update_keycloak_users(keycloak_url, client_id, client_secret, realm)

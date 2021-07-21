from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from devel.auth.constants import (STAFF_ROLE, DEVOPS_ROLE,
                                  OIDC_TRUSTEDUSER_GROUP, OIDC_DEVELOPER_GROUP,
                                  OIDC_MIRRORMAINTAINER_GROUP, OIDC_RELEASEMAINTAINER_GROUP,
                                  OIDC_TESTERS_GROUP, OIDC_SUPPORTSTAFF_GROUPS,
                                  )
from devel.models import UserProfile
from main.models import Repo

DEVELOPER_REPOS = [
    Repo.objects.get(name='Core'),
    Repo.objects.get(name='Extra'),
    Repo.objects.get(name='Testing'),
    Repo.objects.get(name='Staging'),
    Repo.objects.get(name='Multilib'),
    Repo.objects.get(name='Multilib-Testing'),
    Repo.objects.get(name='Multilib-Staging'),
]

TU_REPOS = [
    Repo.objects.get(name='Community'),
    Repo.objects.get(name='Community-Testing'),
    Repo.objects.get(name='Community-Staging'),
    Repo.objects.get(name='Multilib'),
    Repo.objects.get(name='Multilib-Testing'),
    Repo.objects.get(name='Multilib-Staging'),
]


class MyOIDCAB(OIDCAuthenticationBackend):
    DEVELOPER_GROUP = Group.objects.get(name='Developers')
    TRUSTEDUSER_GROUP = Group.objects.get(name='Trusted Users')
    MIRRORMAINTAINER_GROUP = Group.objects.get(name='Mirror Maintainers')
    SUPPORTSTAFF_GROUP = Group.objects.get(name='Support Staff')
    TESTERS_GROUP = Group.objects.get(name='Testers')

    def update_user_groups(self, user, claims, new=False):
        # TODO: reset groups / repositories if things changed?!
        is_devops = DEVOPS_ROLE in claims.get('roles', [])

        # Groups
        groups = claims.get('groups', [])
        is_tu = OIDC_TRUSTEDUSER_GROUP in groups
        is_dev = OIDC_DEVELOPER_GROUP in groups
        is_mirrormaintainer = OIDC_MIRRORMAINTAINER_GROUP in groups
        is_releasemaintainer = OIDC_RELEASEMAINTAINER_GROUP in groups
        is_supportstaff = any(group for group in OIDC_SUPPORTSTAFF_GROUPS if group in groups)
        is_tester = OIDC_TESTERS_GROUP in groups

        # Set username to sub as this is guarranteed unique
        user.username = claims.get('preferred_username', '')
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')

        if new:
            profile = UserProfile.objects.create(user=user)
            profile.sso_accountid = claims.get('sub', '')
        else:
            profile = UserProfile.objects.filter(sso_accountid=claims.get('sub', '')).first()

        profile.alias = claims.get('preferred_username', '')
        profile.public_email = claims.get('email', '')

        if is_devops:
            user.is_staff = True
            user.is_superuser = True

        if is_tu:
            profile.allowed_repos.add(*TU_REPOS)
            user.groups.add(self.TRUSTEDUSER_GROUP)

        if is_dev:
            profile.allowed_repos.add(*DEVELOPER_REPOS)
            user.groups.add(self.DEVELOPER_GROUP)

        if is_mirrormaintainer:
            user.groups.add(self.MIRRORMAINTAINER_GROUP)
            # Required to visit /admin for creating mirror models
            user.is_staff = True

        if is_releasemaintainer:
            user.groups.add(self.RELEASEMAINTAINER_GROUP)
            # Required to visit /admin for creating mirror models
            user.is_staff = True

        if is_supportstaff:
            user.groups.add(self.SUPPORTSTAFF_GROUP)

        if is_tester:
            user.groups.add(self.TESTERS_GROUP)

        user.save()
        profile.save()

    def create_user(self, claims):
        '''
        Called when a user logs in for the first time to Archweb using OIDC

        Assigns the correct django Groups to the corresponding Groups in Keycloak and
        sets Django admin permissions for everyone in the DevOps role.
        '''

        user = super(MyOIDCAB, self).create_user(claims)

        print("create", user, claims)
        self.update_user_groups(user, claims, new=True)

        return user

    def update_user(self, user, claims):
        '''
        :param user django user
        :param claims: Keycloak object
        Called when a user logins again and already has an existing account.
        '''

        print("update", user, claims)
        self.update_user_groups(user, claims)

        return user

    def verify_claims(self, claims):
        '''
        Verifies if a user should be able to log in to Archweb from Keycloak.
        '''

        print('verify_claims', claims)

        verified = super(MyOIDCAB, self).verify_claims(claims)
        is_staff = STAFF_ROLE in claims.get('roles', [])
        email_verified = claims.get('email_verified', False)

        return verified and is_staff and email_verified

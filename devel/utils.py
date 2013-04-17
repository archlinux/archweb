import re

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import connection
from django.db.models import Count, Q

from main.utils import cache_function
from main.models import Package
from packages.models import PackageRelation

@cache_function(300)
def get_annotated_maintainers():
    maintainers = User.objects.filter(is_active=True).order_by(
            'first_name', 'last_name')

    # annotate the maintainers with # of maintained and flagged packages
    pkg_count_sql = """
SELECT pr.user_id, COUNT(*), COUNT(p.flag_date)
    FROM packages_packagerelation pr
    JOIN packages p
    ON pr.pkgbase = p.pkgbase
    WHERE pr.type = %s
    GROUP BY pr.user_id
"""
    cursor = connection.cursor()
    cursor.execute(pkg_count_sql, [PackageRelation.MAINTAINER])
    results = cursor.fetchall()

    pkg_count = {}
    flag_count = {}
    for k, total, flagged in results:
        pkg_count[k] = total
        flag_count[k] = flagged

    update_count = Package.objects.values_list('packager').order_by(
            'packager').annotate(Count('packager'))
    update_count = dict(update_count)

    for m in maintainers:
        m.package_count = pkg_count.get(m.id, 0)
        m.flagged_count = flag_count.get(m.id, 0)
        m.updated_count = update_count.get(m.id, 0)

    return maintainers


def ignore_does_not_exist(func):
    def new_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return None
    return new_func


class UserFinder(object):
    def __init__(self):
        self.cache = {}
        self.username_cache = {}
        self.email_cache = {}
        self.pgp_cache = {}

    @staticmethod
    @ignore_does_not_exist
    def user_email(name, email):
        if email:
            return User.objects.get(email=email)
        return None

    @staticmethod
    @ignore_does_not_exist
    def username_email(name, email):
        if email and '@' in email:
            # split email addr at '@' symbol, ensure domain matches
            # or is a subdomain of archlinux.org
            # TODO: configurable domain/regex somewhere?
            username, domain = email.split('@', 1)
            if re.match(r'^(.+\.)?archlinux.org$', domain):
                return User.objects.get(username=username)
        return None

    @staticmethod
    @ignore_does_not_exist
    def profile_email(name, email):
        if email:
            return User.objects.get(userprofile__public_email=email)
        return None

    @staticmethod
    @ignore_does_not_exist
    def user_name(name, email):
        # yes, a bit odd but this is the easiest way since we can't always be
        # sure how to split the name. Ensure every 'token' appears in at least
        # one of the two name fields.
        if not name:
            return None
        name_q = Q()
        for token in name.split():
            # ignore quoted parts; e.g. nicknames in strings
            if re.match(r'^[\'"].*[\'"]$', token):
                continue
            name_q &= (Q(first_name__icontains=token) |
                    Q(last_name__icontains=token))
        return User.objects.get(name_q)

    def find(self, userstring):
        '''
        Attempt to find the corresponding User object for a standard
        packager string, e.g. something like
            'A. U. Thor <author@example.com>'.
        We start by searching for a matching email address; we then move onto
        matching by first/last name. If we cannot find a user, then return None.
        '''
        if not userstring:
            return None
        if userstring in self.cache:
            return self.cache[userstring]

        name = email = None

        matches = re.match(r'^([^<]+)? ?<([^>]*)>?', userstring)
        if not matches:
            name = userstring.strip()
        else:
            name = matches.group(1)
            email = matches.group(2)

        user = None
        find_methods = (self.user_email, self.profile_email,
                self.username_email, self.user_name)
        for matcher in find_methods:
            user = matcher(name, email)
            if user is not None:
                break

        self.cache[userstring] = user
        self.email_cache[email] = user
        return user

    def find_by_username(self, username):
        if not username:
            return None
        if username in self.username_cache:
            return self.username_cache[username]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        self.username_cache[username] = user
        return user

    def find_by_email(self, email):
        if not email:
            return None
        if email in self.email_cache:
            return self.email_cache[email]

        user = self.user_email(None, email)
        if user is None:
            user = self.profile_email(None, email)
            if user is None:
                user = self.username_email(None, email)

        self.email_cache[email] = user
        return user

    def find_by_pgp_key(self, pgp_key):
        if not pgp_key:
            return None
        if pgp_key in self.pgp_cache:
            return self.pgp_cache[pgp_key]

        try:
            user = User.objects.get(
                    userprofile__pgp_key__endswith=pgp_key)
        except User.DoesNotExist:
            user = None

        self.pgp_cache[pgp_key] = user
        return user

    def clear_cache(self):
        self.cache = {}
        self.username_cache = {}
        self.email_cache = {}
        self.pgp_cache = {}

# vim: set ts=4 sw=4 et:

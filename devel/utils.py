import re

from django.contrib.auth.models import User
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

    update_count = Package.objects.values_list('packager').annotate(
            Count('packager'))
    update_count = dict(update_count)

    for m in maintainers:
        m.package_count = pkg_count.get(m.id, 0)
        m.flagged_count = flag_count.get(m.id, 0)
        m.updated_count = update_count.get(m.id, 0)

    return maintainers

def find_user(userstring):
    '''
    Attempt to find the corresponding User object for a standard
    packager string, e.g. something like
        'A. U. Thor <author@example.com>'.
    We start by searching for a matching email address; we then move onto
    matching by first/last name. If we cannot find a user, then return None.
    '''
    if userstring in find_user.cache:
        return find_user.cache[userstring]
    matches = re.match(r'^([^<]+)? ?<([^>]*)>', userstring)
    if not matches:
        return None

    user = None
    name = matches.group(1)
    email = matches.group(2)

    def user_email():
        return User.objects.get(email=email)
    def profile_email():
        return User.objects.get(userprofile__public_email=email)
    def user_name():
        # yes, a bit odd but this is the easiest way since we can't always be
        # sure how to split the name. Ensure every 'token' appears in at least
        # one of the two name fields.
        name_q = Q()
        for token in name.split():
            # ignore quoted parts; e.g. nicknames in strings
            if re.match(r'^[\'"].*[\'"]$', token):
                continue
            name_q &= (Q(first_name__icontains=token) |
                    Q(last_name__icontains=token))
        return User.objects.get(name_q)

    for matcher in (user_email, profile_email, user_name):
        try:
            user = matcher()
            break
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            pass

    find_user.cache[userstring] = user
    return user

# cached mappings of user strings -> User objects so we don't have to do the
# lookup more than strictly necessary.
find_user.cache = {}

# vim: set ts=4 sw=4 et:

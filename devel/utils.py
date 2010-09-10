from django.contrib.auth.models import User
from django.db import connection

from main.utils import cache_function
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

    for m in maintainers:
        m.package_count = pkg_count.get(m.id, 0)
        m.flagged_count = flag_count.get(m.id, 0)

    return maintainers

# vim: set ts=4 sw=4 et:

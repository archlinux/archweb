from django.db import connections, router

from .models import Todolist, TodolistPackage
from packages.models import Package


def todo_counts():
    sql = """
SELECT todolist_id, count(*), sum(CASE WHEN status = %s THEN 1 ELSE 0 END)
    FROM todolists_todolistpackage
    WHERE removed IS NULL
    GROUP BY todolist_id
    """
    database = router.db_for_write(TodolistPackage)
    connection = connections[database]
    cursor = connection.cursor()
    cursor.execute(sql, [TodolistPackage.COMPLETE])
    results = cursor.fetchall()
    return {row[0]: (row[1], row[2]) for row in results}


def get_annotated_todolists(incomplete_only=False):
    lists = Todolist.objects.all().defer('raw').select_related(
            'creator').order_by('-created')
    lookup = todo_counts()

    # tag each list with package counts
    for todolist in lists:
        counts = lookup.get(todolist.id, (0, 0))
        todolist.pkg_count = counts[0]
        todolist.complete_count = counts[1]
        todolist.incomplete_count = counts[0] - counts[1]

    if incomplete_only:
        lists = [l for l in lists if l.incomplete_count > 0]

    return lists


def attach_staging(packages, list_id):
    '''Look for any staging version of the packages provided and attach them
    to the 'staging' attribute on each package if found.'''
    pkgnames = TodolistPackage.objects.filter(
            todolist_id=list_id).values('pkgname')
    staging_pkgs = Package.objects.normal().filter(repo__staging=True,
            pkgname__in=pkgnames)
    # now build a lookup dict to attach to the correct package
    lookup = {(p.pkgname, p.arch): p for p in staging_pkgs}

    annotated = []
    for package in packages:
        in_staging = lookup.get((package.pkgname, package.arch), None)
        package.staging = in_staging

    return annotated

# vim: set ts=4 sw=4 et:

from django.db import connections, router

from packages.models import Package

from .models import Todolist, TodolistPackage


def todo_counts():
    sql = """
SELECT tp.todolist_id, count(*), SUM(CASE WHEN tp.progress > t.progress THEN 1 ELSE 0 END)
    FROM todolists_todolistpackage tp
    JOIN todolists_todolist t ON t.id = tp.todolist_id
    WHERE tp.removed IS NULL
    GROUP BY tp.todolist_id
    """
    database = router.db_for_write(TodolistPackage)
    connection = connections[database]
    cursor = connection.cursor()
    cursor.execute(sql)
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
        # all packages of a finished list are complete
        todolist.complete_count = counts[0] if todolist.finished else counts[1]
        todolist.incomplete_count = counts[0] - todolist.complete_count

    if incomplete_only:
        lists = [lst for lst in lists if not lst.finished]
    else:
        lists = sorted(lists, key=lambda todolist: todolist.finished)
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
        in_staging = lookup.get((package.pkgname, package.arch))
        package.staging = in_staging

    return annotated

# vim: set ts=4 sw=4 et:

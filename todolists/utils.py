from django.db import connections, router

from packages.models import Package

from .models import Todolist, TodolistPackage


def todo_counts():
    sql = """
SELECT todolist_id, count(*), SUM(CASE WHEN status = %s THEN 1 ELSE 0 END)
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
        lists = [lst for lst in lists if lst.incomplete_count > 0]
    else:
        lists = sorted(lists, key=lambda todolist: todolist.incomplete_count == 0)
    return lists


def _attach_repo_version(packages, list_id, kind):
    '''Look for related packages in repos flagged by kind and attach them.

    kind is a Repo boolean field name used as repo__{kind}=True. Only
    'staging' and 'testing' are used; they set package.staging or
    package.testing for the todolist templates.
    '''
    pkgnames = TodolistPackage.objects.filter(
        todolist_id=list_id).values('pkgname')
    related_pkgs = Package.objects.normal().filter(
        **{f'repo__{kind}': True},
        pkgname__in=pkgnames,
    )
    lookup = {(p.pkgname, p.arch): p for p in related_pkgs}

    for package in packages:
        setattr(package, kind, lookup.get((package.pkgname, package.arch)))


def attach_staging(packages, list_id):
    '''Look for any staging version of the packages provided and attach them
    to the 'staging' attribute on each package if found.'''
    _attach_repo_version(packages, list_id, 'staging')


def attach_testing(packages, list_id):
    '''Look for any testing version of the packages provided and attach them
    to the 'testing' attribute on each package if found.'''
    _attach_repo_version(packages, list_id, 'testing')

# vim: set ts=4 sw=4 et:

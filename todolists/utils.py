from django.db.models import Count

from main.models import Todolist


def get_annotated_todolists():
    qs = Todolist.objects.all()
    lists = qs.select_related('creator').defer(
            'creator__email', 'creator__password', 'creator__is_staff',
            'creator__is_active', 'creator__is_superuser',
            'creator__last_login', 'creator__date_joined').annotate(
            pkg_count=Count('todolistpkg')).order_by('-date_added')
    incomplete = qs.filter(todolistpkg__complete=False).annotate(
            Count('todolistpkg')).values_list('id', 'todolistpkg__count')

    # tag each list with an incomplete package count
    lookup = dict(incomplete)
    for todolist in lists:
        todolist.incomplete_count = lookup.get(todolist.id, 0)

    return lists

# vim: set ts=4 sw=4 et:

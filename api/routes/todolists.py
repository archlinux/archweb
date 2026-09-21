from django.shortcuts import get_object_or_404
from ninja import Router

from api.routes.packages import _pkg_to_schema
from api.schemas.todolists import TodolistPackageSchema, TodolistSchema
from todolists.models import Todolist

router = Router(tags=["todolists"])


@router.get("/{slug}/", response=TodolistSchema, url_name="todolist-details")
def todolist_details(request, slug: str):
    todolist = get_object_or_404(Todolist, slug=slug)
    return TodolistSchema(
        id=todolist.pk,
        name=todolist.name,
        description=todolist.description,
        created=todolist.created,
        last_modified=todolist.last_modified,
        packages=[
            TodolistPackageSchema(
                **_pkg_to_schema(tpkg.pkg).dict(),
                status_str=tpkg.status_str,
            )
            for tpkg in todolist.packages() if tpkg.pkg
        ],
        kind=todolist.kind_str,
    )

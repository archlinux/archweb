import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router

from api.schemas.todolists import TodolistSchema
from todolists.models import Todolist
from todolists.views import TodoListJSONEncoder

router = Router(tags=["todolists"])


@router.get("/{slug}/", response=TodolistSchema, url_name="todolist-details")
def todolist_details(request, slug: str):
    # Same as with /todo/{slug}/json
    todolist = get_object_or_404(Todolist, slug=slug)
    to_json = json.dumps(todolist, ensure_ascii=False, cls=TodoListJSONEncoder)
    return HttpResponse(to_json, content_type='application/json')

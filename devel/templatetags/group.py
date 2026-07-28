from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter(name='in_group')
def in_group(user: User, group_name: str) -> bool:
    return user.groups.filter(name=group_name).exists()


@register.filter(name='in_groups')
def in_groups(user: User, group_names: str) -> bool:
    names = group_names.split(':')
    return user.groups.filter(name__in=names).exists()

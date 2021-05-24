from django import template

register = template.Library()


@register.filter(name='in_group')
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='in_groups')
def in_groups(user, group_names):
    group_names = group_names.split(':')
    return user.groups.filter(name__in=group_names).exists()

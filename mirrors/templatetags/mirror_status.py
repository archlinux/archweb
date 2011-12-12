from datetime import timedelta
from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def duration(value):
    if not value and type(value) != timedelta:
        return u''
    # does not take microseconds into account
    total_secs = value.seconds + value.days * 24 * 3600
    mins = total_secs // 60
    hrs, mins = divmod(mins, 60)
    return '%d:%02d' % (hrs, mins)

@register.filter
def hours(value):
    if not value and type(value) != timedelta:
        return u''
    # does not take microseconds into account
    total_secs = value.seconds + value.days * 24 * 3600
    mins = total_secs // 60
    hrs, mins = divmod(mins, 60)
    if hrs == 1:
        return '%d hour' % hrs
    return '%d hours' % hrs

@register.filter
def percentage(value, arg=-1):
    if not value and type(value) != float:
        return u''
    new_val = value * 100.0
    return floatformat(new_val, arg) + '%'

# vim: set ts=4 sw=4 et:

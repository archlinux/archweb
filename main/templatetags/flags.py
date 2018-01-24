from datetime import timedelta
from django import template

register = template.Library()


@register.simple_tag
def country_flag(country):
    if not country:
        return ''
    return '<span class="fam-flag fam-flag-%s" title="%s"></span> ' % (
            unicode(country.code).lower(), unicode(country.name))

@register.filter
def duration(value):
    if not value and type(value) != timedelta:
        return u''
    # does not take microseconds into account
    total_secs = value.seconds + value.days * 24 * 3600
    mins = total_secs // 60
    hrs, mins = divmod(mins, 60)
    return '%d:%02d' % (hrs, mins)


# vim: set ts=4 sw=4 et:

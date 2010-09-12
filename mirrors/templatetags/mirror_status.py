from django import template

register = template.Library()

@register.filter
def duration(value):
    if not value:
        return u'\u221e'
    # does not take microseconds into account
    total_secs = value.seconds + value.days * 24 * 3600
    mins, secs = divmod(total_secs, 60)
    hrs, mins = divmod(mins, 60)
    return '%d:%02d' % (hrs, mins)

# vim: set ts=4 sw=4 et:

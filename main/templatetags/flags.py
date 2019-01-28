from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def country_flag(country):
    if not country:
        return ''
    return format_html('<span class="fam-flag fam-flag-%s" title="%s"></span> ' % (
            str(country.code).lower(), str(country.name)))


# vim: set ts=4 sw=4 et:

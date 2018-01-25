from django import template

register = template.Library()


@register.simple_tag
def country_flag(country):
    if not country:
        return ''
    return '<span class="fam-flag fam-flag-%s" title="%s"></span> ' % (
            unicode(country.code).lower(), unicode(country.name))


# vim: set ts=4 sw=4 et:

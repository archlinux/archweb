from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def jquery():
    version = '3.6.0'
    filename = f'jquery-{version}.min.js'
    link = staticfiles_storage.url(filename)
    return mark_safe(f'<script type="text/javascript" src="{link}"></script>')


@register.simple_tag
def jquery_tablesorter():
    version = '2.31.0'
    filename = f'jquery.tablesorter-{version}.min.js'
    link = staticfiles_storage.url(filename)
    return format_html('<script type="text/javascript" src="{link}"></script>', link=link)


@register.simple_tag
def d3js():
    version = '3.5.0'
    filename = f'd3-{version}.min.js'
    link = staticfiles_storage.url(filename)
    return format_html('<script type="text/javascript" src="{link}"></script>', link=link)

# vim: set ts=4 sw=4 et:

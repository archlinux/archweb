from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()


@register.simple_tag
def retro_static(year, path):
    """Like the built-in {% static %} tag but with a little extra magic."""
    full_path = "%s/%s" % (year, path)
    return staticfiles_storage.url(full_path)

# vim: set ts=4 sw=4 et:

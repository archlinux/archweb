from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def jquery():
    version = '1.4.4'
    oncdn = getattr(settings, 'CDN_ENABLED', True)
    if oncdn:
        link = 'https://ajax.googleapis.com/ajax/libs/jquery/' \
                '%s/jquery.min.js' % version
    else:
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        link = '%sjquery-%s.min.js' % (static_url, version)
    return '<script type="text/javascript" src="%s"></script>' % link

# vim: set ts=4 sw=4 et:

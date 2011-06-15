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
        link = '/media/jquery-%s.min.js' % version
    return '<script type="text/javascript" src="%s"></script>' % link

@register.tag
def cdnprefix(parser, token):
    return CDNPrefixNode()

class CDNPrefixNode(template.Node):
    def render(self, context):
        oncdn = getattr(settings, 'CDN_ENABLED', True)
        if not oncdn:
            return ''
        secure = 'secure' in context and context['secure']
        # if left undefined, same behavior as if CDN is turned off
        paths = {
                False: getattr(settings, 'CDN_PATH', ''),
                True: getattr(settings, 'CDN_PATH_SECURE', ''),
        }
        return paths[secure]

# vim: set ts=4 sw=4 et:

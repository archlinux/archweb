from django import template
from django.conf import settings

register = template.Library()

@register.tag
def jquery(parser, token):
    return JQueryNode()

class JQueryNode(template.Node):
    def render(self, context):
        # if we have the request in context, we can check if it is secure and
        # serve content from HTTPS instead.
        secure = 'request' in context and context['request'].is_secure()
        version = '1.4.2'
        oncdn = getattr(settings, 'CDN_ENABLED', True)
        if oncdn and secure:
            jquery = 'https://ajax.googleapis.com/ajax/libs/jquery/%s/jquery.min.js' % version
        elif oncdn:
            jquery = 'http://ajax.googleapis.com/ajax/libs/jquery/%s/jquery.min.js' % version
        else:
            jquery = '/media/jquery-%s.min.js' % version
        return '<script type="text/javascript" src="%s"></script>' % jquery

# vim: set ts=4 sw=4 et:

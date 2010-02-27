from django import template
from django.conf import settings

register = template.Library()

@register.tag
def jquery(parser, token):
    return JQueryNode()

class JQueryNode(template.Node):
    def render(self, context):
        version = '1.4.1'
        if getattr(settings, 'DEBUG', True):
            jquery = '/media/jquery-%s.min.js' % version
        else:
            jquery = 'http://ajax.googleapis.com/ajax/libs/jquery/%s/jquery.min.js' % version
        return '<script type="text/javascript" src="%s"></script>' % jquery

# vim: set ts=4 sw=4 et:

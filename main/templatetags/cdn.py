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
        secure = 'secure' in context and context['secure']
        prefixes = { False: 'http', True: 'https' }
        version = '1.4.2'
        oncdn = getattr(settings, 'CDN_ENABLED', True)
        if oncdn:
            jquery = '%s://ajax.googleapis.com/ajax/libs/jquery/' \
                    '%s/jquery.min.js' % (prefixes[secure], version)
        else:
            jquery = '/media/jquery-%s.min.js' % version
        return '<script type="text/javascript" src="%s"></script>' % jquery

# vim: set ts=4 sw=4 et:

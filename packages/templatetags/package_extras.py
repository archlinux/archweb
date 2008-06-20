from django import template

register = template.Library()

class BuildQueryStringNode(template.Node):
    def __init__(self, sortfield):
        self.sortfield = sortfield
    def render(self, context):
        qs = context['querystring'].copy()
        if qs.has_key('sort') and qs['sort'] == self.sortfield:
            if self.sortfield.startswith('-'):
                qs['sort'] = self.sortfield[1:]
            else:
                qs['sort'] = '-' + self.sortfield
        else:
            qs['sort'] = self.sortfield
        return '?' + qs.urlencode()

@register.tag(name='buildsortqs')
def do_buildsortqs(parser, token):
    try:
        tagname, sortfield = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % tagname
    if not (sortfield[0] == sortfield[-1] and sortfield[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tagname
    return BuildQueryStringNode(sortfield[1:-1])

@register.filter(name='space2br')
def space2br(value):
    return value.replace(' ', '<br />')

# vim: set ts=4 sw=4 et:


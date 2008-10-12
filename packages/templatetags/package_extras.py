import cgi, urllib
from django import template

register = template.Library()

class BuildQueryStringNode(template.Node):
    def __init__(self, sortfield):
        self.sortfield = sortfield

    def render(self, context):
        qs = dict(cgi.parse_qsl(context['current_query'][1:]))
        if qs.has_key('sort') and qs['sort'] == self.sortfield:
            if self.sortfield.startswith('-'):
                qs['sort'] = self.sortfield[1:]
            else:
                qs['sort'] = '-' + self.sortfield
        else:
            qs['sort'] = self.sortfield
        return '?' + urllib.urlencode(qs)

@register.tag(name='buildsortqs')
def do_buildsortqs(parser, token):
    try:
        tagname, sortfield = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
                "%r tag requires a single argument" % tagname)
    if not (sortfield[0] == sortfield[-1] and sortfield[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
                "%r tag's argument should be in quotes" % tagname)
    return BuildQueryStringNode(sortfield[1:-1])

@register.inclusion_tag('forms/td_input.html')
def td_input(form_element):
    return {'form_element': form_element}


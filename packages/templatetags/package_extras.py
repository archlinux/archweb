import cgi, urllib
from django import template
from django.utils.html import escape

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

@register.simple_tag
def userpkgs(user):
    if user:
        # TODO don't hardcode
        title = escape('View packages maintained by ' + user.get_full_name())
        return '<a href="/packages/?maintainer=%s" title="%s">%s</a>' % (
                user.username,
                title,
                user.get_full_name(),
        )
    return ''

# vim: set ts=4 sw=4 et:

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

@register.tag
def userpkgs(parser, token):
    try:
        tagname, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
                "%r tag requires a single argument" % tagname)
    return UserPkgsNode(user)

class UserPkgsNode(template.Node):
    def __init__(self, user):
        self.user = template.Variable(user)

    def render(self, context):
        try:
            real_user = self.user.resolve(context)
			# TODO don't hardcode
            return '<a href="/packages/search/?maintainer=%s">%s</a>' % (
					real_user.username, real_user.get_full_name())
        except template.VariableDoesNotExist:
            return ''
        pass

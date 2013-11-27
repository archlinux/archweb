from urllib import urlencode, quote as urlquote, unquote
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

from django import template
from django.utils.html import escape

register = template.Library()


def link_encode(url, query):
    # massage the data into all utf-8 encoded strings first, so urlencode
    # doesn't barf at the data we pass it
    query = {k: unicode(v).encode('utf-8') for k, v in query.items()}
    data = urlencode(query).replace('&', '&amp;')
    return "%s?%s" % (url, data)


@register.filter
def url_unquote(original_url):
    try:
        url = original_url
        if isinstance(url, unicode):
            url = url.encode('ascii')
        url = unquote(url).decode('utf-8')
        return url
    except UnicodeError:
        return original_url


class BuildQueryStringNode(template.Node):
    def __init__(self, sortfield):
        self.sortfield = sortfield
        super(BuildQueryStringNode, self).__init__()

    def render(self, context):
        qs = parse_qs(context['current_query'])
        # This is really dirty. The crazy round trips we do on our query string
        # mean we get things like u'\xe2\x98\x83' in our views, when we should
        # have simply u'\u2603' or a byte string of the UTF-8 value. Force the
        # keys and list of values to be byte strings only.
        qs = {k.encode('latin-1'): [v.encode('latin-1') for v in vals]
                for k, vals in qs.items()}
        if 'sort' in qs and self.sortfield in qs['sort']:
            if self.sortfield.startswith('-'):
                qs['sort'] = [self.sortfield[1:]]
            else:
                qs['sort'] = ['-' + self.sortfield]
        else:
            qs['sort'] = [self.sortfield]
        return urlencode(qs, True).replace('&', '&amp;')


@register.tag(name='buildsortqs')
def do_buildsortqs(parser, token):
    try:
        tagname, sortfield = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
                "%r tag requires a single argument" % token)
    if not (sortfield[0] == sortfield[-1] and sortfield[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
                "%r tag's argument should be in quotes" % token)
    return BuildQueryStringNode(sortfield[1:-1])


@register.simple_tag
def pkg_details_link(pkg, link_title=None, honor_flagged=False):
    if not pkg:
        return link_title or ''
    if link_title is None:
        link_title = pkg.pkgname
    link_content = link_title
    if honor_flagged and pkg.flag_date:
        link_content = '<span class="flagged">%s</span>' % link_title
    link = '<a href="%s" title="View package details for %s">%s</a>'
    return link % (pkg.get_absolute_url(), pkg.pkgname, link_content)


@register.simple_tag
def multi_pkg_details(pkgs):
    return ', '.join([pkg_details_link(pkg) for pkg in pkgs])


@register.simple_tag
def maintainer_link(user):
    if user:
        # TODO don't hardcode
        title = escape('View packages maintained by ' + user.get_full_name())
        return '<a href="/packages/?maintainer=%s" title="%s">%s</a>' % (
                user.username,
                title,
                user.get_full_name(),
        )
    return ''


@register.simple_tag
def packager_link(user):
    if user:
        # TODO don't hardcode
        title = escape('View packages packaged by ' + user.get_full_name())
        return '<a href="/packages/?packager=%s" title="%s">%s</a>' % (
                user.username,
                title,
                user.get_full_name(),
        )
    return ''


@register.simple_tag
def scm_link(package, operation):
    parts = (package.repo.svn_root, operation, package.pkgbase)
    linkbase = (
        "https://projects.archlinux.org/svntogit/%s.git/%s/trunk?"
        "h=packages/%s")
    return linkbase % tuple(urlquote(part.encode('utf-8')) for part in parts)


@register.simple_tag
def get_wiki_link(package):
    url = "https://wiki.archlinux.org/index.php/Special:Search"
    data = {
        'search': package.pkgname,
    }
    return link_encode(url, data)


@register.simple_tag
def bugs_list(package):
    url = "https://bugs.archlinux.org/"
    data = {
        'project': package.repo.bugs_project,
        'cat[]': package.repo.bugs_category,
        'string': package.pkgname,
    }
    return link_encode(url, data)


@register.simple_tag
def bug_report(package):
    url = "https://bugs.archlinux.org/newtask"
    data = {
        'project': package.repo.bugs_project,
        'product_category': package.repo.bugs_category,
        'item_summary': '[%s] PLEASE ENTER SUMMARY' % package.pkgname,
    }
    return link_encode(url, data)

# vim: set ts=4 sw=4 et:

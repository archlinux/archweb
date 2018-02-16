from urllib.parse import urlencode, quote as urlquote, unquote
from django import template
from main.templatetags import pgp

register = template.Library()


def link_encode(url, query):
    # massage the data into all utf-8 encoded strings first, so urlencode
    # doesn't barf at the data we pass it
    query = {k: str(v).encode('utf-8') for k, v in list(query.items())}
    data = urlencode(query)
    return "%s?%s" % (url, data)


@register.inclusion_tag('packages/details_link.html')
def details_link(pkg):
    return {'pkg': pkg}


@register.simple_tag
def scm_link(package, operation):
    parts = (package.repo.svn_root, operation, package.pkgbase)
    linkbase = (
        "https://projects.archlinux.org/svntogit/%s.git/%s/trunk?"
        "h=packages/%s")
    return linkbase % tuple(urlquote(part.encode('utf-8')) for part in parts)


@register.simple_tag
def bugs_list(package):
    url = "https://bugs.archlinux.org/"
    data = {
        'project': package.repo.bugs_project,
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


@register.simple_tag
def wiki_link(package):
    url = "https://wiki.archlinux.org/index.php/Special:Search"
    data = {
        'search': package.pkgname,
    }
    return link_encode(url, data)

@register.simple_tag
def sec_link(package):
    url = "https://security.archlinux.org/package/{}"
    return url.format(package.pkgname)

@register.simple_tag
def pgp_key_link(key_id, link_text=None):
    return pgp.pgp_key_link(key_id, link_text)


@register.filter
def url_unquote(original_url):
    try:
        url = original_url
        if isinstance(url, str):
            url = url.encode('ascii')
        url = unquote(url).decode('utf-8')
        return url
    except UnicodeError:
        return original_url

# vim: set ts=4 sw=4 et:

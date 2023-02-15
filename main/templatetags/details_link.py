from urllib.parse import urlencode, quote as urlquote, unquote
from django import template
from django.conf import settings
from main.templatetags import pgp
from main.utils import gitlab_project_name_to_path

register = template.Library()


def link_encode(url, query):
    # massage the data into all utf-8 encoded strings first, so urlencode
    # doesn't barf at the data we pass it
    query = {k: str(v).encode('utf-8') for k, v in query.items()}
    data = urlencode(query)
    return "%s?%s" % (url, data)


@register.inclusion_tag('packages/details_link.html')
def details_link(pkg):
    return {'pkg': pkg}


@register.simple_tag
def scm_link(package, operation: str):
    pkgbase = urlquote(gitlab_project_name_to_path(package.pkgbase))
    if operation == 'tree':
        return f'{settings.GITLAB_PACKAGES_REPO}/{pkgbase}/'
    elif operation == 'commits':
        return f'{settings.GITLAB_PACKAGES_REPO}/{pkgbase}/-/commits/main'


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
    url = "https://wiki.archlinux.org/title/Special:Search"
    data = {
        'search': package.pkgname,
    }
    return link_encode(url, data)


@register.simple_tag
def man_link(package):
    url = "https://man.archlinux.org/listing/{}"
    return url.format(package.pkgname)


@register.simple_tag
def sec_link(package):
    url = "https://security.archlinux.org/package/{}"
    return url.format(package.pkgname)


@register.simple_tag
def rebuilderd_diffoscope_link(rbstatus):
    url = "https://reproducible.archlinux.org/api/v0/builds/{}/diffoscope"
    return url.format(rbstatus.build_id)


@register.simple_tag
def rebuilderd_buildlog_link(rbstatus):
    url = "https://reproducible.archlinux.org/api/v0/builds/{}/log"
    return url.format(rbstatus.build_id)


@register.simple_tag
def pgp_key_link(key_id, link_text=None):
    return pgp.pgp_key_link(key_id, link_text)


@register.filter
def url_unquote(original_url):
    return unquote(original_url)

# vim: set ts=4 sw=4 et:

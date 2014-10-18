from urllib import urlencode, quote as urlquote, unquote
from django.utils.html import escape
from django_jinja import library
from main.templatetags import pgp


@library.filter
def url_unquote(original_url):
    try:
        url = original_url
        if isinstance(url, unicode):
            url = url.encode('ascii')
        url = unquote(url).decode('utf-8')
        return url
    except UnicodeError:
        return original_url


def link_encode(url, query):
    # massage the data into all utf-8 encoded strings first, so urlencode
    # doesn't barf at the data we pass it
    query = {k: unicode(v).encode('utf-8') for k, v in query.items()}
    data = urlencode(query)
    return "%s?%s" % (url, data)


@library.global_function
def pgp_key_link(key_id, link_text=None):
    return pgp.pgp_key_link(key_id, link_text)


@library.global_function
def scm_link(package, operation):
    parts = (package.repo.svn_root, operation, package.pkgbase)
    linkbase = (
        "https://projects.archlinux.org/svntogit/%s.git/%s/trunk?"
        "h=packages/%s")
    return linkbase % tuple(urlquote(part.encode('utf-8')) for part in parts)


@library.global_function
def wiki_link(package):
    url = "https://wiki.archlinux.org/index.php/Special:Search"
    data = {
        'search': package.pkgname,
    }
    return link_encode(url, data)


@library.global_function
def bugs_list(package):
    url = "https://bugs.archlinux.org/"
    data = {
        'project': package.repo.bugs_project,
        'cat[]': package.repo.bugs_category,
        'string': package.pkgname,
    }
    return link_encode(url, data)


@library.global_function
def bug_report(package):
    url = "https://bugs.archlinux.org/newtask"
    data = {
        'project': package.repo.bugs_project,
        'product_category': package.repo.bugs_category,
        'item_summary': '[%s] PLEASE ENTER SUMMARY' % package.pkgname,
    }
    return link_encode(url, data)


# vim: set ts=4 sw=4 et:

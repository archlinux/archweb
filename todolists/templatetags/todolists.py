from django import template
from django.utils.html import format_html

register = template.Library()


def pkg_absolute_url(repo, arch, pkgname):
    return '/packages/%s/%s/%s/' % (repo.name.lower(), arch.name, pkgname)


@register.simple_tag
def todopkg_details_link(todopkg):
    pkg = todopkg.pkg
    if not pkg:
        return todopkg.pkgname
    link = '<a href={url}s" title="View package details for {pkgname}">{pkgname}</a>'
    url = pkg_absolute_url(todopkg.repo, todopkg.arch, pkg.pkgname)
    return format_html(link, url=url, pkgname=pkg.pkgname)


# vim: set ts=4 sw=4 et:

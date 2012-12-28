from django import template

register = template.Library()


def pkg_absolute_url(repo, arch, pkgname):
    return '/packages/%s/%s/%s/' % (repo.name.lower(), arch.name, pkgname)


@register.simple_tag
def todopkg_details_link(todopkg):
    pkg = todopkg.pkg
    if not pkg:
        return todopkg.pkgname
    link = '<a href="%s" title="View package details for %s">%s</a>'
    url = pkg_absolute_url(todopkg.repo, todopkg.arch, pkg.pkgname)
    return link % (url, pkg.pkgname, pkg.pkgname)

# vim: set ts=4 sw=4 et:

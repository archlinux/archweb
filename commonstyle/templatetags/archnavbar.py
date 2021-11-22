from os import path
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()


@register.simple_tag
def archnavbar():
    with open(path.join(settings.DEPLOY_PATH, "commonstyle", "archlinux-common-style", "html", "navbar.html"), "r", encoding="UTF-8") as f:
        return mark_safe(
            f.read()
            .replace('href="https://archlinux.org"', 'href="/"')
            .replace('href="https://archlinux.org/packages/"', 'href="/packages/"')
        )

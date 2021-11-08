from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def archnavbar():
    with open("./commonstyle/archlinux-common-style/html/navbar.html", "r", encoding="UTF-8") as f:
        return mark_safe(
                f.read()
                    .replace('href="https://archlinux.org"', 'href="/"')
                    .replace('href="https://archlinux.org/packages/"', 'href="/packages/"')
            )

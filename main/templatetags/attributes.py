import re
from typing import Any

from django import template

numeric_test = re.compile(r"^\d+$")
register = template.Library()


def attribute(value: Any, arg: str) -> Any:
    """Gets an attribute of an object dynamically from a string name"""
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return ""


register.filter('attribute', attribute)

# vim: set ts=4 sw=4 et:

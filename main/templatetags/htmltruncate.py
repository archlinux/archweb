import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import escape
from django.utils.text import TruncateWordsHTMLParser

register = template.Library()


class PrePreservingTruncateWordsHTMLParser(TruncateWordsHTMLParser):
    """
    Like Django's TruncateWordsHTMLParser, but text inside <pre> keeps its
    original whitespace (truncatewords_html collapses newlines to spaces).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pre_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'pre':
            self._pre_depth += 1
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag.lower() == 'pre':
            self._pre_depth = max(0, self._pre_depth - 1)

    def process(self, data):
        if self._pre_depth <= 0:
            return super().process(data)
        parts = re.split(r'(?<=\S)\s+(?=\S)', data)
        if not data:
            return [], ''
        if len(parts) <= self.remaining:
            return parts, escape(data)
        output = escape(' '.join(parts[: self.remaining]))
        return parts, output


@register.filter(is_safe=True)
@stringfilter
def truncatewords_html_preserve_pre(value, arg):
    try:
        length = int(arg)
    except ValueError:
        return value
    if length <= 0:
        return ''
    parser = PrePreservingTruncateWordsHTMLParser(length=length, replacement=' …')
    parser.feed(value)
    parser.close()
    return parser.output

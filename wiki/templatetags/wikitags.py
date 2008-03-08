from django.template import Library
from django.conf import settings
from archweb_dev.main import markdown
import re

register = Library()

class WikiProcessor:
    def run(self, lines):
        in_table = False
        for i in range(len(lines)):
            # Linebreaks
            lines[i] = re.sub("%%", "<br />", lines[i])
            # Internal Links
            lines[i] = re.sub("\(\(([A-z0-9 :/-]+)\)\)", "<a href=\"/wiki/\\1\">\\1</a>", lines[i])
            # Small Text
            lines[i] = re.sub("----([^----]+)----", "<span style=\"font-size:x-small\">\\1</span>", lines[i])
            lines[i] = re.sub("--([^--]+)--",       "<span style=\"font-size:small\">\\1</span>", lines[i])
            # TT text
            lines[i] = re.sub("\{\{([^}\}]+)\}\}",  "<tt>\\1</tt>", lines[i])
            # Tables
            m = re.match("(\|\|)", lines[i])
            if m:
                count = len(re.findall("(\|\|+)", lines[i]))
                first = True
                m2 = re.search("(\|\|+)", lines[i])
                while m2 and count:
                    count -= 1
                    colspan = len(m2.group(1)) / 2
                    if first:
                        repl = "<td colspan=\"%d\">" % (colspan)
                        first = False
                    elif count == 0:
                        repl = "</td>"
                    else:
                        repl = "</td><td colspan=\"%d\">" % (colspan)
                    lines[i] = re.sub("(\|\|+)", repl, lines[i], 1)
                    # find the next chunk
                    m2 = re.search("(\|\|+)", lines[i])
                lines[i] = "<tr>" + lines[i] + "</tr>"
                if not in_table:
                    lines[i] = "<table>" + lines[i]
                    in_table = True
            elif in_table:
                lines[i] = "</table>" + lines[i]
                in_table = False
        # close leftover table, if open
        if in_table:
            lines[len(lines)] = lines[len(lines)] + "</table>"
        return lines

@register.filter
def wikify(value):
    md = markdown.Markdown(value)
    md.preprocessors.insert(0, WikiProcessor())
    html = md.toString()
    return html

# vim: set ts=4 sw=4 et:


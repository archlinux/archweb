import re
import urllib
from HTMLParser import HTMLParser, HTMLParseError

from django.core.management.base import BaseCommand, CommandError

from isotests.models import Iso
from settings import ISOLISTURL

class IsoListParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

        self.hyperlinks = []
        self.url_re = re.compile('(?!\.{2})/$')

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == "href":
                    if value != '../' and self.url_re.search(value) != None:
                        self.hyperlinks.append(value[:len(value)-1])

    def parse(self, url):
        try:
            f = urllib.urlopen(url)

            s = f.read()
            f.close()

            self.feed(s)
            self.close()

            return self.hyperlinks
        except HTMLParseError:
            raise CommandError('Couldn\'t parse "%s"' % url)

class Command(BaseCommand):
    help = 'Gets new isos from http://releng.archlinux.org/isos/'

    def handle(self, *args, **options):
        parser = IsoListParser()
        isonames = Iso.objects.values_list('name', flat=True)
        new_isos = parser.parse(ISOLISTURL)

        for iso in new_isos:
            if iso not in isonames:
                new = Iso(name=iso)
                new.save()

# vim: set ts=4 sw=4 et:

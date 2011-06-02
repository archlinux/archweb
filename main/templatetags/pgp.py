from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def pgp_key_link(key_id):
    if not key_id:
        return "Unknown"
    # Something like 'pgp.mit.edu:11371'
    pgp_server = getattr(settings, 'PGP_SERVER', None)
    if not pgp_server:
        return "0x%s" % key_id
    url = 'http://%s/pks/lookup?op=vindex&fingerprint=on&exact=on&search=0x%s' % \
            (pgp_server, key_id)
    values = (url, key_id, key_id)
    return '<a href="%s" title="PGP key search for 0x%s">0x%s</a>' % values

# vim: set ts=4 sw=4 et:

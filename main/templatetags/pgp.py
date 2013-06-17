from django import template
from django.conf import settings
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from devel.models import DeveloperKey

register = template.Library()


def format_key(key_id):
    if len(key_id) in (8, 20):
        return u'0x%s' % key_id
    elif len(key_id) == 40:
        # normal display format is 5 groups of 4 hex chars seperated by spaces,
        # double space, then 5 more groups of 4 hex chars
        split = tuple(key_id[i:i+4] for i in range(0, 40, 4))
        return u'%s\u00a0 %s' % (' '.join(split[0:5]), ' '.join(split[5:10]))
    return u'0x%s' % key_id

@register.simple_tag
def pgp_key_link(key_id, link_text=None):
    if not key_id:
        return "Unknown"
    if isinstance(key_id, (int, long)):
        key_id = '%X' % key_id
        # zero-fill to nearest 8, 16, or 40 chars if necessary
        if len(key_id) <= 8:
            key_id = key_id.zfill(8)
        elif len(key_id) <= 16:
            key_id = key_id.zfill(16)
        elif len(key_id) <= 40:
            key_id = key_id.zfill(40)
    # Something like 'pgp.mit.edu:11371'
    pgp_server = getattr(settings, 'PGP_SERVER', None)
    if not pgp_server:
        return format_key(key_id)
    url = 'http://%s/pks/lookup?op=vindex&amp;fingerprint=on&amp;exact=on&amp;search=0x%s' % \
            (pgp_server, key_id)
    if link_text is None:
        link_text = '0x%s' % key_id[-8:]
    values = (url, format_key(key_id), link_text)
    return '<a href="%s" title="PGP key search for %s">%s</a>' % values

@register.simple_tag
def user_pgp_key_link(key_id):
    normalized = key_id[-16:]
    try:
        matching_key = DeveloperKey.objects.select_related(
                'owner').get(key=normalized, owner_id__isnull=False)
    except DeveloperKey.DoesNotExist:
        return pgp_key_link(key_id)
    return pgp_key_link(key_id, matching_key.owner.get_full_name())


@register.filter(needs_autoescape=True)
def pgp_fingerprint(key_id, autoescape=True):
    if not key_id:
        return u''
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(format_key(esc(key_id)))


@register.assignment_tag
def signature_exists(signatures, signer, signee):
    if not signer or not signee:
        return False
    lookup = (signer[-16:], signee[-16:])
    return lookup in signatures

# vim: set ts=4 sw=4 et:

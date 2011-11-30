from django.db import models
from django.contrib.auth.models import User

from main.fields import PGPKeyField


class MasterKey(models.Model):
    owner = models.ForeignKey(User, related_name='masterkey_owner',
        help_text="The developer holding this master key")
    revoker = models.ForeignKey(User, related_name='masterkey_revoker',
        help_text="The developer holding the revocation certificate")
    pgp_key = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    created = models.DateTimeField()
    revoked = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('created',)

# vim: set ts=4 sw=4 et:

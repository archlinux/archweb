# -*- coding: utf-8 -*-
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

    def __unicode__(self):
        return u'%s, created %s' % (
                self.owner.get_full_name(), self.created)


class PGPSignature(models.Model):
    signer = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    signee = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    created = models.DateField()
    expires = models.DateField(null=True, blank=True)
    valid = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'PGP signature'

    def __unicode__(self):
        return u'%s → %s' % (self.signer, self.signee)

# vim: set ts=4 sw=4 et:

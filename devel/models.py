# -*- coding: utf-8 -*-
import pytz

from django.db import models
from django.contrib.auth.models import User

from .fields import PGPKeyField
from main.utils import make_choice


class UserProfile(models.Model):
    notify = models.BooleanField(
        "Send notifications",
        default=True,
        help_text="When enabled, send user 'flag out-of-date' notifications")
    time_zone = models.CharField(
        max_length=100,
        choices=make_choice(pytz.common_timezones),
        default="UTC",
        help_text="Used for developer clock page")
    alias = models.CharField(
        max_length=50,
        help_text="Required field")
    public_email = models.CharField(
        max_length=50,
        help_text="Required field")
    other_contact = models.CharField(max_length=100, null=True, blank=True)
    pgp_key = PGPKeyField(max_length=40, null=True, blank=True,
        verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    website = models.CharField(max_length=200, null=True, blank=True)
    yob = models.IntegerField("Year of birth", null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    languages = models.CharField(max_length=50, null=True, blank=True)
    interests = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    roles = models.CharField(max_length=255, null=True, blank=True)
    favorite_distros = models.CharField(max_length=255, null=True, blank=True)
    picture = models.FileField(upload_to='devs', default='devs/silhouette.png',
        help_text="Ideally 125px by 125px")
    user = models.OneToOneField(User, related_name='userprofile')
    allowed_repos = models.ManyToManyField('main.Repo', blank=True)
    latin_name = models.CharField(max_length=255, null=True, blank=True,
        help_text="Latin-form name; used only for non-Latin full names")

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Additional Profile Data'
        verbose_name_plural = 'Additional Profile Data'

    def get_absolute_url(self):
        # TODO: this is disgusting. find a way to consolidate this logic with
        # public.views.userlist among other places, and make some constants or
        # something so we aren't using copies of string names everywhere.
        group_names = self.user.groups.values_list('name', flat=True)
        if "Developers" in group_names:
            prefix = "developers"
        elif "Trusted Users" in group_names:
            prefix = "trustedusers"
        else:
            prefix = "fellows"
        return '/%s/#%s' % (prefix, self.user.username)



class MasterKey(models.Model):
    owner = models.ForeignKey(User, related_name='masterkey_owner',
        help_text="The developer holding this master key")
    revoker = models.ForeignKey(User, related_name='masterkey_revoker',
        help_text="The developer holding the revocation certificate")
    pgp_key = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    created = models.DateField()
    revoked = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return u'%s, created %s' % (
                self.owner.get_full_name(), self.created)


class PGPSignature(models.Model):
    signer = PGPKeyField(max_length=40, verbose_name="Signer key fingerprint")
    signee = PGPKeyField(max_length=40, verbose_name="Signee key fingerprint")
    created = models.DateField()
    expires = models.DateField(null=True, blank=True)
    valid = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'PGP signature'

    def __unicode__(self):
        return u'%s → %s' % (self.signer, self.signee)

# vim: set ts=4 sw=4 et:

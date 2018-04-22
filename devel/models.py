# -*- coding: utf-8 -*-
import pytz

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.contrib.auth.models import User, Group
from django_countries.fields import CountryField

from .fields import PGPKeyField
from main.utils import make_choice, set_created_field


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
    country = CountryField(blank=True)
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
    last_modified = models.DateTimeField(editable=False)

    class Meta:
        db_table = 'user_profiles'
        get_latest_by = 'last_modified'
        verbose_name = 'additional profile data'
        verbose_name_plural = 'additional profile data'

    def get_absolute_url(self):
        user = self.user
        group = StaffGroup.objects.filter(group=user.groups.all().first()).get()
        if group:
            return '%s#%s' % (group.get_absolute_url(), user.username)
        return None


class StaffGroup(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    group = models.OneToOneField(Group)
    sort_order = models.PositiveIntegerField()
    member_title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('sort_order',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('people', args=[self.slug])


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
        get_latest_by = 'created'

    def __str__(self):
        return '%s, created %s' % (
                self.owner.get_full_name(), self.created)


class DeveloperKey(models.Model):
    owner = models.ForeignKey(User, related_name='all_keys', null=True,
            help_text="The developer this key belongs to")
    key = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint",
            unique=True)
    created = models.DateTimeField()
    expires = models.DateTimeField(null=True, blank=True)
    revoked = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.key


class PGPSignature(models.Model):
    signer = PGPKeyField(max_length=40, verbose_name="Signer key fingerprint",
            db_index=True)
    signee = PGPKeyField(max_length=40, verbose_name="Signee key fingerprint",
            db_index=True)
    created = models.DateField()
    expires = models.DateField(null=True, blank=True)
    revoked = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('signer', 'signee')
        get_latest_by = 'created'
        verbose_name = 'PGP signature'

    def __str__(self):
        return '%s → %s' % (self.signer, self.signee)


pre_save.connect(set_created_field, sender=UserProfile,
        dispatch_uid="devel.models")

# vim: set ts=4 sw=4 et:

# -*- coding: utf-8 -*-
import zoneinfo

from django.contrib.auth.models import Group, User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.urls import reverse
from django_countries.fields import CountryField

from main.utils import make_choice, set_created_field
from planet.models import Feed

from .fields import PGPKeyField


class UserProfile(models.Model):
    latin_name = models.CharField(
        max_length=255, null=True, blank=True, help_text="Latin-form name; used only for non-Latin full names")
    notify = models.BooleanField(
        "Send notifications",
        default=True,
        help_text="When enabled, send user 'flag out-of-date' notifications")
    time_zone = models.CharField(
        max_length=100,
        choices=make_choice(sorted(zoneinfo.available_timezones())),  # sort as available_timezones output varies
        default="UTC",
        help_text="Used for developer clock page")
    alias = models.CharField(
        max_length=50,
        help_text="Required field")
    public_email = models.EmailField(
        max_length=50,
        help_text="Required field")
    other_contact = models.CharField(max_length=100, null=True, blank=True)
    pgp_key = PGPKeyField(
        max_length=40, null=True, blank=True,
        verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    website = models.URLField(max_length=200, null=True, blank=True)
    website_rss = models.URLField(max_length=200, null=True, blank=True,
                                  help_text='RSS Feed of your website for planet.archlinux.org')
    social = models.URLField(max_length=200, null=True, blank=True,
                             verbose_name="Social account URL",
                             help_text="Mastodon or Fediverse account URL")
    yob = models.IntegerField("Year of birth", null=True, blank=True,
                              validators=[MinValueValidator(1950), MaxValueValidator(2500)])
    country = CountryField(blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    languages = models.CharField(max_length=50, null=True, blank=True)
    interests = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    roles = models.CharField(max_length=255, null=True, blank=True)
    favorite_distros = models.CharField(max_length=255, null=True, blank=True)
    picture = models.FileField(
        upload_to='devs', default='devs/silhouette.png', help_text="Ideally 125px by 125px")
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    allowed_repos = models.ManyToManyField('main.Repo', blank=True)
    rebuilderd_updates = models.BooleanField(
        default=False, help_text='Receive reproducible build package updates')
    repos_auth_token = models.CharField(max_length=32, null=True, blank=True)
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
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
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
    owner = models.ForeignKey(
        User, related_name='masterkey_owner',
        help_text="The developer holding this master key",
        on_delete=models.CASCADE)
    revoker = models.ForeignKey(
        User, related_name='masterkey_revoker',
        help_text="The developer holding the revocation certificate",
        on_delete=models.CASCADE)
    pgp_key = PGPKeyField(
        max_length=40, verbose_name="PGP key fingerprint",
        help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    created = models.DateField()
    revoked = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('created',)
        get_latest_by = 'created'

    def __str__(self):
        return '%s, created %s' % (self.owner.get_full_name(), self.created)


class DeveloperKey(models.Model):
    owner = models.ForeignKey(
        User, related_name='all_keys', null=True,
        help_text="The developer this key belongs to",
        on_delete=models.CASCADE)
    key = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint", unique=True)
    created = models.DateTimeField()
    expires = models.DateTimeField(null=True, blank=True)
    revoked = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.key


class PGPSignature(models.Model):
    signer = PGPKeyField(max_length=40, verbose_name="Signer key fingerprint", db_index=True)
    signee = PGPKeyField(max_length=40, verbose_name="Signee key fingerprint", db_index=True)
    created = models.DateField()
    expires = models.DateField(null=True, blank=True)
    revoked = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('signer', 'signee')
        get_latest_by = 'created'
        verbose_name = 'PGP signature'

    def __str__(self):
        return '%s → %s' % (self.signer, self.signee)


def create_feed_model(sender, **kwargs):
    allowed_groups = ['Developers', 'Package Maintainers', 'Support Staff']

    set_created_field(sender, **kwargs)

    obj = kwargs['instance']

    if not obj.id:
        return

    dbmodel = UserProfile.objects.get(id=obj.id)
    groups = dbmodel.user.groups.filter(name__in=allowed_groups)

    # Only Staff is allowed to publish on planet
    if len(groups) == 0:
        return

    if not obj.website_rss and dbmodel.website_rss:
        Feed.objects.filter(website_rss=dbmodel.website_rss).all().delete()
        return

    if not obj.website_rss:
        return

    if obj.website:
        website = obj.website
    else:
        from urllib.parse import urlparse
        parsed = urlparse(obj.website_rss)
        website = obj.website_rss.replace(parsed.path, '')

    # Nothing changed
    if obj.website_rss == dbmodel.website_rss:
        return

    title = obj.alias
    if obj.user.first_name and obj.user.last_name:
        title = obj.user.first_name + ' ' + obj.user.last_name

    # Remove old feeds
    Feed.objects.filter(website_rss=dbmodel.website_rss).all().delete()
    Feed.objects.create(title=title, website=website,
                        website_rss=obj.website_rss)


def delete_user_model(sender, **kwargs):
    '''When a user is set to inactive remove his feed model and repository token'''

    obj = kwargs['instance']

    if not obj.id:
        return

    if obj.is_active:
        return

    userprofile = UserProfile.objects.filter(user=obj).first()
    if not userprofile:
        return

    userprofile.repos_auth_token = ''

    Feed.objects.filter(website_rss=userprofile.website_rss).delete()


pre_save.connect(create_feed_model, sender=UserProfile, dispatch_uid="devel.models")

post_save.connect(delete_user_model, sender=User, dispatch_uid='main.models')

# vim: set ts=4 sw=4 et:

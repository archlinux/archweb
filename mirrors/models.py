import socket
from urlparse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django_countries import CountryField

from .fields import IPNetworkField
from main.utils import set_created_field


class Mirror(models.Model):
    TIER_CHOICES = (
        (0, 'Tier 0'),
        (1, 'Tier 1'),
        (2, 'Tier 2'),
        (-1, 'Untiered'),
    )

    name = models.CharField(max_length=255, unique=True)
    tier = models.SmallIntegerField(default=2, choices=TIER_CHOICES)
    upstream = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    admin_email = models.EmailField(max_length=255, blank=True)
    alternate_email = models.EmailField(max_length=255, blank=True)
    public = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    isos = models.BooleanField("ISOs", default=True)
    rsync_user = models.CharField(max_length=50, blank=True, default='')
    rsync_password = models.CharField(max_length=50, blank=True, default='')
    notes = models.TextField(blank=True)
    created = models.DateTimeField(editable=False)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def downstream(self):
        return Mirror.objects.filter(upstream=self).order_by('name')

    def get_absolute_url(self):
        return '/mirrors/%s/' % self.name


class MirrorProtocol(models.Model):
    protocol = models.CharField(max_length=10, unique=True)
    is_download = models.BooleanField(default=True,
            help_text="Is protocol useful for end-users, e.g. HTTP")
    default = models.BooleanField(default=True,
            help_text="Included by default when building mirror list?")
    created = models.DateTimeField(editable=False)

    def __unicode__(self):
        return self.protocol

    class Meta:
        ordering = ('protocol',)


class MirrorUrl(models.Model):
    url = models.CharField("URL", max_length=255, unique=True)
    protocol = models.ForeignKey(MirrorProtocol, related_name="urls",
            editable=False, on_delete=models.PROTECT)
    mirror = models.ForeignKey(Mirror, related_name="urls")
    country = CountryField(blank=True, db_index=True)
    has_ipv4 = models.BooleanField("IPv4 capable", default=True,
            editable=False)
    has_ipv6 = models.BooleanField("IPv6 capable", default=False,
            editable=False)
    created = models.DateTimeField(editable=False)
    active = models.BooleanField(default=True)

    def address_families(self):
        hostname = urlparse(self.url).hostname
        info = socket.getaddrinfo(hostname, None, 0, socket.SOCK_STREAM)
        families = [x[0] for x in info]
        return families

    @property
    def hostname(self):
        return urlparse(self.url).hostname

    def clean(self):
        try:
            # Auto-map the protocol field by looking at the URL
            protocol = urlparse(self.url).scheme
            self.protocol = MirrorProtocol.objects.get(protocol=protocol)
        except Exception as e:
            raise ValidationError(e)
        try:
            families = self.address_families()
            self.has_ipv4 = socket.AF_INET in families
            self.has_ipv6 = socket.AF_INET6 in families
        except socket.error:
            # We don't fail in this case; we'll just set both to False
            self.has_ipv4 = False
            self.has_ipv6 = False

    def __unicode__(self):
        return self.url

    class Meta:
        verbose_name = 'mirror URL'


class MirrorRsync(models.Model):
    # max length is 40 chars for full-form IPv6 addr + subnet
    ip = IPNetworkField("IP")
    mirror = models.ForeignKey(Mirror, related_name="rsync_ips")
    created = models.DateTimeField(editable=False)

    def __unicode__(self):
        return self.ip

    class Meta:
        verbose_name = 'mirror rsync IP'
        ordering = ('ip',)


class CheckLocation(models.Model):
    hostname = models.CharField(max_length=255)
    source_ip = models.GenericIPAddressField(verbose_name='source IP',
            unpack_ipv4=True, unique=True)
    country = CountryField()
    created = models.DateTimeField(editable=False)

    class Meta:
        ordering = ('hostname', 'source_ip')

    def __unicode__(self):
        return self.hostname

    @property
    def family(self):
        info = socket.getaddrinfo(self.source_ip, None, 0, 0, 0,
                socket.AI_NUMERICHOST)
        families = [x[0] for x in info]
        return families[0]

    @property
    def ip_version(self):
        '''Returns integer '4' or '6'.'''
        if self.family == socket.AF_INET6:
            return 6
        if self.family == socket.AF_INET:
            return 4
        return None


class MirrorLog(models.Model):
    url = models.ForeignKey(MirrorUrl, related_name="logs")
    location = models.ForeignKey(CheckLocation, related_name="logs", null=True)
    check_time = models.DateTimeField(db_index=True)
    last_sync = models.DateTimeField(null=True)
    duration = models.FloatField(null=True)
    is_success = models.BooleanField(default=True)
    error = models.TextField(blank=True, default='')

    def __unicode__(self):
        return "Check of %s at %s" % (self.url.url, self.check_time)

    class Meta:
        verbose_name = 'mirror check log'
        get_latest_by = 'check_time'


for model in (Mirror, MirrorProtocol, MirrorUrl, MirrorRsync, CheckLocation):
    pre_save.connect(set_created_field, sender=model,
            dispatch_uid="mirrors.models")

# vim: set ts=4 sw=4 et:

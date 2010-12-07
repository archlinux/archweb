from django.db import models

TIER_CHOICES = (
    (0, 'Tier 0'),
    (1, 'Tier 1'),
    (2, 'Tier 2'),
    (-1, 'Untiered'),
)

class Mirror(models.Model):
    name = models.CharField(max_length=255)
    tier = models.SmallIntegerField(default=2, choices=TIER_CHOICES)
    upstream = models.ForeignKey('self', null=True)
    country = models.CharField(max_length=255, db_index=True)
    admin_email = models.EmailField(max_length=255, blank=True)
    public = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    isos = models.BooleanField(default=True)
    rsync_user = models.CharField(max_length=50, blank=True, default='')
    rsync_password = models.CharField(max_length=50, blank=True, default='')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('country', 'name')

    def __unicode__(self):
        return self.name

    def supported_protocols(self):
        protocols = MirrorProtocol.objects.filter(
                urls__mirror=self).order_by('protocol').distinct()
        return ", ".join([p.protocol for p in protocols])

    def downstream(self):
        return Mirror.objects.filter(upstream=self).order_by('name')

    def get_absolute_url(self):
        return '/mirrors/%s/' % self.name

class MirrorProtocol(models.Model):
    protocol = models.CharField(max_length=10, unique=True)
    is_download = models.BooleanField(default=True,
            help_text="Is protocol useful for end-users, e.g. FTP/HTTP")

    def __unicode__(self):
        return self.protocol

    class Meta:
        verbose_name = 'Mirror Protocol'

class MirrorUrl(models.Model):
    url = models.CharField(max_length=255)
    protocol = models.ForeignKey(MirrorProtocol, related_name="urls")
    mirror = models.ForeignKey(Mirror, related_name="urls")
    has_ipv4 = models.BooleanField("IPv4 capable", default=True)
    has_ipv6 = models.BooleanField("IPv6 capable", default=False)

    def __unicode__(self):
        return self.url

    class Meta:
        verbose_name = 'Mirror URL'

class MirrorRsync(models.Model):
    ip = models.CharField(max_length=24)
    mirror = models.ForeignKey(Mirror, related_name="rsync_ips")

    def __unicode__(self):
        return "%s" % (self.ip)

    class Meta:
        verbose_name = 'Mirror Rsync IP'

class MirrorLog(models.Model):
    url = models.ForeignKey(MirrorUrl, related_name="logs")
    check_time = models.DateTimeField(db_index=True)
    last_sync = models.DateTimeField(null=True)
    duration = models.FloatField(null=True)
    is_success = models.BooleanField(default=True)
    error = models.CharField(max_length=255, blank=True, default='')

    def __unicode__(self):
        return "Check of %s at %s" % (self.url.url, self.check_time)

    class Meta:
        verbose_name = 'Mirror Check Log'

# vim: set ts=4 sw=4 et:

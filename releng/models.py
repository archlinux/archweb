from base64 import b64decode
from bencode import bdecode, bencode
from datetime import datetime
import hashlib
import markdown
from pytz import utc

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.utils.safestring import mark_safe

from main.fields import PositiveBigIntegerField
from main.utils import set_created_field


class IsoOption(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class RollbackOption(IsoOption):
    class Meta:
        abstract = True


class Iso(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(editable=False)
    removed = models.DateTimeField(null=True, blank=True, default=None)
    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse('releng-results-iso', args=[self.pk])

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'ISO'


class Architecture(IsoOption):
    pass


class IsoType(IsoOption):
    class Meta:
        verbose_name = 'ISO type'


class BootType(IsoOption):
    pass


class HardwareType(IsoOption):
    pass


class InstallType(IsoOption):
    pass


class Source(IsoOption):
    pass


class ClockChoice(IsoOption):
    pass


class Filesystem(RollbackOption):
    pass


class Module(RollbackOption):
    pass


class Bootloader(IsoOption):
    pass


class Test(models.Model):
    user_name = models.CharField(max_length=500)
    user_email = models.EmailField('email address')
    # Great work, Django... https://code.djangoproject.com/ticket/18212
    ip_address = models.GenericIPAddressField(verbose_name='IP address',
            unpack_ipv4=True)
    created = models.DateTimeField(editable=False)

    iso = models.ForeignKey(Iso)
    architecture = models.ForeignKey(Architecture)
    iso_type = models.ForeignKey(IsoType)
    boot_type = models.ForeignKey(BootType)
    hardware_type = models.ForeignKey(HardwareType)
    install_type = models.ForeignKey(InstallType)
    source = models.ForeignKey(Source)
    clock_choice = models.ForeignKey(ClockChoice)
    filesystem = models.ForeignKey(Filesystem)
    modules = models.ManyToManyField(Module, null=True, blank=True)
    bootloader = models.ForeignKey(Bootloader)
    rollback_filesystem = models.ForeignKey(Filesystem,
            related_name="rollback_test_set", null=True, blank=True)
    rollback_modules = models.ManyToManyField(Module,
            related_name="rollback_test_set", null=True, blank=True)

    success = models.BooleanField()
    comments = models.TextField(null=True, blank=True)


class Release(models.Model):
    release_date = models.DateField(db_index=True)
    version = models.CharField(max_length=50, unique=True)
    kernel_version = models.CharField(max_length=50, blank=True)
    torrent_infohash = models.CharField(max_length=40, blank=True)
    md5_sum = models.CharField('MD5 digest', max_length=32, blank=True)
    sha1_sum = models.CharField('SHA1 digest', max_length=40, blank=True)
    file_size = PositiveBigIntegerField(null=True, blank=True)
    created = models.DateTimeField(editable=False)
    available = models.BooleanField(default=True)
    info = models.TextField('Public information', blank=True)
    torrent_data = models.TextField(blank=True)

    class Meta:
        get_latest_by = 'release_date'
        ordering = ('-release_date', '-version')

    def __unicode__(self):
        return self.version

    def get_absolute_url(self):
        return reverse('releng-release-detail', args=[self.version])

    def dir_path(self):
        return "iso/%s/" % self.version

    def iso_url(self):
        return "iso/%s/archlinux-%s-dual.iso" % (self.version, self.version)

    def magnet_uri(self):
        query = [
            ('dn', "archlinux-%s-dual.iso" % self.version),
        ]
        if settings.TORRENT_TRACKERS:
            query.extend(('tr', uri) for uri in settings.TORRENT_TRACKERS)
        if self.torrent_infohash:
            query.insert(0, ('xt', "urn:btih:%s" % self.torrent_infohash))
        return "magnet:?%s" % '&'.join(['%s=%s' % (k, v) for k, v in query])

    def info_html(self):
        return mark_safe(markdown.markdown(
            self.info, safe_mode=True, enable_attributes=False))

    def torrent(self):
        try:
            data = b64decode(self.torrent_data.encode('utf-8'))
        except TypeError:
            return None
        if not data:
            return None
        data = bdecode(data)
        # transform the data into a template-friendly dict
        info = data.get('info', {})
        metadata = {
            'comment': data.get('comment', None),
            'created_by': data.get('created by', None),
            'creation_date': None,
            'announce': data.get('announce', None),
            'file_name': info.get('name', None),
            'file_length': info.get('length', None),
            'piece_count': len(info.get('pieces', '')) / 20,
            'piece_length': info.get('piece length', None),
            'url_list': data.get('url-list', []),
            'info_hash': None,
        }
        if 'creation date' in data:
            created= datetime.utcfromtimestamp(data['creation date'])
            metadata['creation_date'] = created.replace(tzinfo=utc)
        if info:
            metadata['info_hash'] = hashlib.sha1(bencode(info)).hexdigest()

        return metadata


for model in (Iso, Test, Release):
    pre_save.connect(set_created_field, sender=model,
            dispatch_uid="releng.models")

# vim: set ts=4 sw=4 et:

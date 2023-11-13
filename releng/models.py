import binascii
import hashlib
from base64 import b64decode
from datetime import datetime, timezone

from bencode import bdecode, bencode
from django.db import models
from django.db.models.signals import pre_save
from django.urls import reverse
from django.utils.safestring import mark_safe

from devel.fields import PGPKeyField
from main.utils import parse_markdown, set_created_field


class Release(models.Model):
    release_date = models.DateField(db_index=True)
    version = models.CharField(max_length=50, unique=True)
    kernel_version = models.CharField(max_length=50, blank=True)
    md5_sum = models.CharField('MD5 digest', max_length=32, blank=True)
    sha1_sum = models.CharField('SHA1 digest', max_length=40, blank=True)
    sha256_sum = models.CharField('SHA256 digest', max_length=64, blank=True)
    b2_sum = models.CharField('BLAKE2b digest', max_length=128, blank=True)
    pgp_key = PGPKeyField(max_length=40, verbose_name="PGP key fingerprint",  null=True, blank=True,
                          help_text="consists of 40 hex digits; use `gpg --fingerprint`")
    wkd_email = models.EmailField(max_length=254, null=True, blank=True)
    created = models.DateTimeField(editable=False)
    last_modified = models.DateTimeField(editable=False)
    available = models.BooleanField(default=True)
    info = models.TextField('Public information', blank=True)
    torrent_data = models.TextField(blank=True, help_text="base64-encoded torrent file")

    class Meta:
        get_latest_by = 'release_date'
        ordering = ('-release_date', '-version')

    def __str__(self):
        return self.version

    def get_absolute_url(self):
        return reverse('releng-release-detail', args=[self.version])

    def dir_path(self):
        return "iso/%s/" % self.version

    def iso_url(self):
        return "iso/%s/archlinux-%s-x86_64.iso" % (self.version, self.version)

    def tarball_url(self):
        return "iso/%s/archlinux-bootstrap-%s-x86_64.tar.gz" % (self.version, self.version)

    def dir_url(self):
        return "iso/%s" % (self.version)

    def magnet_uri(self):
        query = [
            ('dn', "archlinux-%s-x86_64.iso" % self.version),
        ]
        metadata = self.torrent()
        if metadata and 'info_hash' in metadata:
            query.insert(0, ('xt', "urn:btih:%s" % metadata['info_hash']))
        return "magnet:?%s" % '&'.join(['%s=%s' % (k, v) for k, v in query])

    def info_html(self):
        return mark_safe(parse_markdown(self.info))

    def torrent(self):
        try:
            data = b64decode(self.torrent_data.encode('utf-8'))
        except (TypeError, binascii.Error):
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
            metadata['creation_date'] = datetime.fromtimestamp(data['creation date'], tz=timezone.utc)
        if info:
            metadata['info_hash'] = hashlib.sha1(bencode(info)).hexdigest()

        return metadata


pre_save.connect(set_created_field, sender=Release, dispatch_uid="releng.models")

# vim: set ts=4 sw=4 et:

from base64 import b64decode
from bencode import bdecode, bencode
from datetime import datetime
import hashlib
from pytz import utc

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.utils.safestring import mark_safe

from main.utils import set_created_field, parse_markdown


class Release(models.Model):
    release_date = models.DateField(db_index=True)
    version = models.CharField(max_length=50, unique=True)
    kernel_version = models.CharField(max_length=50, blank=True)
    md5_sum = models.CharField('MD5 digest', max_length=32, blank=True)
    sha1_sum = models.CharField('SHA1 digest', max_length=40, blank=True)
    created = models.DateTimeField(editable=False)
    last_modified = models.DateTimeField(editable=False)
    available = models.BooleanField(default=True)
    info = models.TextField('Public information', blank=True)
    torrent_data = models.TextField(blank=True,
            help_text="base64-encoded torrent file")

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

    def magnet_uri(self):
        query = [
            ('dn', "archlinux-%s-x86_64.iso" % self.version),
        ]
        if settings.TORRENT_TRACKERS:
            query.extend(('tr', uri) for uri in settings.TORRENT_TRACKERS)
        metadata = self.torrent()
        if metadata and 'info_hash' in metadata:
            query.insert(0, ('xt', "urn:btih:%s" % metadata['info_hash']))
        return "magnet:?%s" % '&'.join(['%s=%s' % (k, v) for k, v in query])

    def info_html(self):
        return mark_safe(parse_markdown(self.info))

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


pre_save.connect(set_created_field, sender=Release, dispatch_uid="releng.models")

# vim: set ts=4 sw=4 et:

from base64 import b64encode
from datetime import datetime, timezone

import pytest
from bencode import bencode

from releng.models import Release

VERSION = '1.0'
KERNEL_VERSION = '4.18'

# Sample signing identity; same values as releng/fixtures/release.json (PGPKeyField stores 40 hex digits).
PGP_KEY_FINGERPRINT = '3E80CA1A8B89F69CBA57D98A76A5EF9054449A5C'
WKD_EMAIL = 'pierre@archlinux.de'


@pytest.fixture
def release(db):
    release = Release.objects.create(
        release_date=datetime.now(),
        version=VERSION,
        kernel_version=KERNEL_VERSION,
        pgp_key=PGP_KEY_FINGERPRINT,
        wkd_email=WKD_EMAIL,
    )
    yield release
    release.delete()


@pytest.fixture
def torrent_data():
    data = {
        'comment': 'comment',
        'created_by': 'Arch Linux',
        'creation date': int(datetime.now(timezone.utc).timestamp()),
        'info': {
            'name': 'arch.iso',
            'length': 1,
        }
    }
    return b64encode(bencode(data)).decode()

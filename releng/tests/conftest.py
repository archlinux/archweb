from base64 import b64encode
from datetime import datetime

import pytest
from bencode import bencode

from releng.models import Release

VERSION = '1.0'
KERNEL_VERSION = '4.18'


@pytest.fixture
def release(db):
    release = Release.objects.create(release_date=datetime.now(),
                                     version=VERSION,
                                     kernel_version=KERNEL_VERSION)
    yield release
    release.delete()


@pytest.fixture
def torrent_data():
    data = {
        'comment': 'comment',
        'created_by': 'Arch Linux',
        'creation date': int(datetime.utcnow().timestamp()),
        'info': {
            'name': 'arch.iso',
            'length': 1,
        }
    }
    return b64encode(bencode(data)).decode()

from datetime import datetime

import pytest

from releng.models import Release


VERSION = '1.0'
KERNEL_VERSION = '4.18'


@pytest.fixture
def release(db):
    release =  Release.objects.create(release_date=datetime.now(),
                                      version=VERSION,
                                      kernel_version=KERNEL_VERSION)
    yield release
    release.delete()

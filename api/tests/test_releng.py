from datetime import datetime, timezone

import pytest

from releng.models import Release

VERSION = '2025.05.01'
KERNEL_VERSION = '6.9'


@pytest.fixture
def release(db):
    r = Release.objects.create(
        release_date=datetime.now(timezone.utc),
        version=VERSION,
        kernel_version=KERNEL_VERSION,
        available=True,
    )
    yield r
    r.delete()


def test_releases_empty(db, client):
    response = client.get('/api/v1/releng/releases/')
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == 1
    assert data['releases'] == []
    assert data['latest_version'] is None


def test_releases_returns_release_fields(client, release):
    response = client.get('/api/v1/releng/releases/')
    assert response.status_code == 200
    r = response.json()['releases'][0]
    assert r['version'] == VERSION
    assert r['kernel_version'] == KERNEL_VERSION
    assert r['available'] is True


def test_releases_latest_version_is_newest_available(db, client):
    now = datetime.now(timezone.utc)
    Release.objects.create(release_date=now, version='2025.01.01', available=True)
    Release.objects.create(release_date=now, version='2025.05.01', available=True)
    data = client.get('/api/v1/releng/releases/').json()
    assert data['latest_version'] == '2025.05.01'


def test_releases_latest_version_excludes_unavailable(db, client):
    now = datetime.now(timezone.utc)
    Release.objects.create(release_date=now, version='2025.01.01', available=True)
    Release.objects.create(release_date=now, version='2025.05.01', available=False)
    data = client.get('/api/v1/releng/releases/').json()
    assert data['latest_version'] == '2025.01.01'


def test_releases_optional_fields_null_when_absent(db, client):
    Release.objects.create(
        release_date=datetime.now(timezone.utc),
        version='2025.05.01',
    )
    r = client.get('/api/v1/releng/releases/').json()['releases'][0]
    assert r['kernel_version'] is None
    assert r['md5_sum'] is None
    assert r['sha1_sum'] is None
    assert r['sha256_sum'] is None
    assert r['b2_sum'] is None

import pytest

from mirrors.tests.conftest import (  # noqa: F401
    checklocation,
    create_mirrorurl,
    mirror,
    mirrorprotocol,
    mirrorurl,
)


@pytest.fixture
def public_active_mirror(mirror):  # noqa: F811
    mirror.public = True
    mirror.active = True
    mirror.save()
    return mirror


def test_status_empty(db, client):
    response = client.get('/api/v1/mirrors/status/')
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == 3
    assert data['urls'] == []
    assert data['num_checks'] == 0


def test_status_tier_invalid(db, client):
    response = client.get('/api/v1/mirrors/status/tier/999/')
    assert response.status_code == 404


def test_status_tier_valid_empty(db, client):
    response = client.get('/api/v1/mirrors/status/tier/0/')
    assert response.status_code == 200
    assert response.json()['version'] == 3


def test_status_includes_active_public_mirror_url(
    db, client, public_active_mirror, mirrorprotocol  # noqa: F811
):
    from mirrors.models import MirrorUrl
    url = MirrorUrl.objects.create(
        url='https://example.org/',
        protocol=mirrorprotocol,
        mirror=public_active_mirror,
        country='DE',
        active=True,
    )
    response = client.get('/api/v1/mirrors/status/')
    assert response.status_code == 200
    urls = response.json()['urls']
    assert len(urls) == 1
    assert urls[0]['url'] == 'https://example.org/'
    assert urls[0]['protocol'] == 'https'
    assert urls[0]['country_code'] == 'DE'
    url.delete()


def test_locations_empty(db, client):
    response = client.get('/api/v1/mirrors/locations/')
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == 1
    assert data['locations'] == []


def test_locations_returns_checklocation(db, client, checklocation):  # noqa: F811
    response = client.get('/api/v1/mirrors/locations/')
    assert response.status_code == 200
    locs = response.json()['locations']
    assert len(locs) == 1
    assert locs[0]['hostname'] == 'archlinux.org'
    assert locs[0]['country_code'] == 'DE'


def test_mirror_details_not_found(db, client):
    response = client.get('/api/v1/mirrors/does-not-exist/')
    assert response.status_code == 404


def test_mirror_details_private_returns_404(db, client, mirror):  # noqa: F811
    mirror.public = False
    mirror.save()
    response = client.get(f'/api/v1/mirrors/{mirror.name}/')
    assert response.status_code == 404


def test_mirror_details_public_returns_data(db, client, public_active_mirror):
    response = client.get(f'/api/v1/mirrors/{public_active_mirror.name}/')
    assert response.status_code == 200
    data = response.json()
    assert data['version'] == 5
    assert data['tier'] == public_active_mirror.tier
    assert 'admin_email' not in data or data['admin_email'] is None

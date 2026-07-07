from mirrors.tests.conftest import mirror  # noqa: F401


def test_releng_releases_json_deprecation_headers(db, client):
    response = client.get('/releng/releases/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/releng/releases/>; rel="successor-version"'


def test_mirror_status_json_deprecation_headers(db, client):
    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/mirrors/status/>; rel="successor-version"'


def test_mirror_status_tier_json_deprecation_headers(db, client):
    response = client.get('/mirrors/status/tier/0/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/mirrors/status/>; rel="successor-version"'


def test_mirror_locations_json_deprecation_headers(db, client):
    response = client.get('/mirrors/locations/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/mirrors/locations/>; rel="successor-version"'


def test_mirror_details_json_deprecation_headers(db, client, mirror):  # noqa: F811
    mirror.public = True
    mirror.active = True
    mirror.save()
    response = client.get(f'/mirrors/{mirror.name}/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/mirrors/{name}/>; rel="successor-version"'

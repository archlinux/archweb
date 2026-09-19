from mirrors.tests.conftest import mirror  # noqa: F401
from todolists.tests.conftest import todolist  # noqa: F401


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


def test_master_keys_json_deprecation_headers(db, client):
    response = client.get('/master-keys/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/master-keys/>; rel="successor-version"'


def test_package_details_json_deprecation_headers(db, client, package):
    response = client.get('/packages/core/x86_64/linux/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == \
        '</api/v1/packages/{repo}/{arch}/{name}/>; rel="successor-version"'


def test_package_files_json_deprecation_headers(db, client, package):
    response = client.get('/packages/core/x86_64/linux/files/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == \
        '</api/v1/packages/{repo}/{arch}/{name}/files/>; rel="successor-version"'


def test_package_sonames_json_deprecation_headers(db, client, package):
    response = client.get('/packages/core/x86_64/linux/sonames/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == \
        '</api/v1/packages/{repo}/{arch}/{name}/sonames/>; rel="successor-version"'


def test_pkgbase_maintainer_deprecation_headers(db, client):
    response = client.get('/packages/pkgbase-maintainer')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == \
        '</api/v1/packages/pkgbase-maintainer>; rel="successor-version"'


def test_package_search_json_deprecation_headers(db, client):
    response = client.get('/packages/search/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/packages/search/>; rel="successor-version"'


def test_todolist_json_deprecation_headers(db, client, todolist):  # noqa: F811
    response = client.get(f'/todo/{todolist.slug}/json')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/todo/{slug}/>; rel="successor-version"'

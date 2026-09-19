import pytest


@pytest.fixture
def linux_pkg(package):
    # linux, repo=Core, arch=x86_64
    return ('core', 'x86_64', 'linux')


def test_details_parity(db, client, linux_pkg):
    repo, arch, name = linux_pkg
    v1 = client.get(f'/api/v1/packages/{repo}/{arch}/{name}/')
    legacy = client.get(f'/packages/{repo}/{arch}/{name}/json/')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()


def test_details_not_found(db, client, repos):
    response = client.get('/api/v1/packages/core/x86_64/does-not-exist/')
    assert response.status_code == 404


def test_files_parity(db, client, linux_pkg):
    repo, arch, name = linux_pkg
    v1 = client.get(f'/api/v1/packages/{repo}/{arch}/{name}/files/')
    legacy = client.get(f'/packages/{repo}/{arch}/{name}/files/json/')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()


def test_sonames_parity(db, client, linux_pkg):
    repo, arch, name = linux_pkg
    v1 = client.get(f'/api/v1/packages/{repo}/{arch}/{name}/sonames/')
    legacy = client.get(f'/packages/{repo}/{arch}/{name}/sonames/json/')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()


def test_pkgbase_maintainer_parity(db, client, linux_pkg):
    v1 = client.get('/api/v1/packages/pkgbase-maintainer')
    legacy = client.get('/packages/pkgbase-maintainer')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()


def test_search_no_params_parity(db, client):
    v1 = client.get('/api/v1/packages/search/')
    legacy = client.get('/packages/search/json/')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    body = v1.json()
    assert body['valid'] is False
    assert body['results'] == []
    assert 'num_pages' not in body  # omitted when query is invalid, like legacy
    assert body == legacy.json()


def test_search_with_query_parity(db, client, linux_pkg):
    v1 = client.get('/api/v1/packages/search/?name=linux')
    legacy = client.get('/packages/search/json/?name=linux')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()


def test_search_bad_page_returns_400(db, client):
    response = client.get('/api/v1/packages/search/?page=notanumber')
    assert response.status_code == 400

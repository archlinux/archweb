def test_feed(db, client):
    response = client.get('/feeds/packages/')
    assert response.status_code == 200


def test_sitemap(db, client):
    for sitemap in ['packages', 'package-groups', 'package-files', 'split-packages']:
        response = client.get('/sitemap-{}.xml'.format(sitemap))
        assert response.status_code == 200


def test_invalid_json(client, package):
    response = client.get('/packages/search/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['limit'] == 250
    assert data['results'] == []
    assert not data['valid']


def test_reponame(client, package):
    response = client.get('/packages/search/json/?repository=core')
    assert response.status_code == 200

    data = response.json()
    assert len(data['results']) == 5
    assert {r['pkgname'] for r in data['results']} == {"coreutils", "glibc", "linux", "pacman", "systemd"}


def test_packagename(client, package):
    response = client.get('/packages/search/json/?name=linux')
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 1


def test_no_results(client, package):
    response = client.get('/packages/search/json/?name=none')
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 0


def test_limit_four(client, package):
    response = client.get('/packages/search/json/?limit=4')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['num_pages'] == 2
    assert data['limit'] == 4
    assert len(data['results']) == 4


def test_second_page(client, package):
    response = client.get('/packages/search/json/?limit=4&page=2')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 2
    assert data['num_pages'] == 2
    assert len(data['results']) == 1


def test_invalid_parameter(client, db):
    response = client.get('/packages/search/json/?page=garbage')
    assert response.status_code == 400


def test_arch_differences(client, package):
    response = client.get('/packages/differences/')
    assert response.status_code == 200


def test_packages_detail(client, package):
    response = client.get('/packages/core/x86_64/linux/')
    assert response.status_code == 200

    response = client.get('/packages/core/x86_64/nope/')
    assert response.status_code == 404

    # Redirect to search
    response = client.get('/packages/core/x86_64/')
    assert response.status_code == 302


def test_packages_json(client, package):
    response = client.get('/packages/core/x86_64/linux/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['pkgbase'] == 'linux'
    # TODO verify more of the structure


def test_packages_files(client, package):
    response = client.get('/packages/core/x86_64/linux/files/')
    assert response.status_code == 200


def test_packages_files_json(client, package):
    response = client.get('/packages/core/x86_64/linux/files/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['pkgname'] == 'linux'
    # TODO verify more of the structure


def test_packages_download(client, package):
    response = client.get('/packages/core/x86_64/linux/download/')
    assert response.status_code == 404
    # TODO: Figure out how to fake a mirror


def test_groups(client, package):
    response = client.get('/groups/')
    assert response.status_code == 200


def test_groups_arch(client, package):
    response = client.get('/groups/x86_64/')
    assert response.status_code == 200


def test_groups_details(client, package):
    response = client.get('/groups/x86_64/base/')
    assert response.status_code == 404
    # FIXME: add group fixtures.


def test_stale_relations(developer_client):
    response = developer_client.get('/packages/stale_relations/')
    assert response.status_code == 200

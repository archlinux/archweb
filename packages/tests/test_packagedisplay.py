def test_packages_detail(client, arches, repos, package):
    response = client.get('/packages/core/x86_64/linux/')
    assert response.status_code == 200

    response = client.get('/packages/core/x86_64/nope/')
    assert response.status_code == 404

    # Redirect to search
    response = client.get('/packages/core/x86_64/')
    assert response.status_code == 302


def test_packages_json(client, arches, repos, package):
    response = client.get('/packages/core/x86_64/linux/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['pkgbase'] == 'linux'
    # TODO verify more of the structure


def test_packages_files(client, arches, repos, package):
    response = client.get('/packages/core/x86_64/linux/files/')
    assert response.status_code == 200


def test_packages_files_json(client, arches, repos, package):
    response = client.get('/packages/core/x86_64/linux/files/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['pkgname'] == 'linux'
    # TODO verify more of the structure


def test_packages_download(client, arches, repos, package):
    response = client.get('/packages/core/x86_64/linux/download/')
    assert response.status_code == 404
    # TODO: Figure out how to fake a mirror


def test_head(client, arches, repos, package):
    response = client.head('/packages/core/x86_64/linux/')
    assert response.status_code == 200


def test_groups(client, arches, repos, package):
    response = client.get('/groups/')
    assert response.status_code == 200


def test_groups_arch(client, arches, repos, package):
    response = client.get('/groups/x86_64/')
    assert response.status_code == 200


def test_groups_details(client, arches, repos, package):
    response = client.get('/groups/x86_64/base/')
    assert response.status_code == 404
    # FIXME: add group fixtures.

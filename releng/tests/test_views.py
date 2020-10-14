def test_release_json(client, release):
    version = release.version
    response = client.get('/releng/releases/json/')
    assert response.status_code == 200

    data = response.json()
    assert data['version'] == 1
    release = data['releases'][0]
    assert release['version'] == version


def test_netboot_page(db, client):
    response = client.get('/releng/netboot/')
    assert response.status_code == 200


def test_netboot_config(db, client):
    response = client.get('/releng/netboot/archlinux.ipxe')
    assert response.status_code == 200


def test_release_torrent_not_found(client, release):
    # TODO: Add torrent data to release fixture
    response = client.get('/releng/releases/{}/torrent/'.format(release.version))
    assert response.status_code == 404


def test_release_details(client, release):
    response = client.get('/releng/releases/{}/'.format(release.version))
    assert response.status_code == 200
    assert release.version in response.content.decode()

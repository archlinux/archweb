def test_release_json(client, release, torrent_data):
    version = release.version
    response = client.get('/releng/releases/json/')
    assert response.status_code == 200

    data = response.json()
    assert data['version'] == 1
    release_data = data['releases'][0]
    assert release_data['version'] == version

    # Test with torrent data
    release.torrent_data = torrent_data
    release.save()
    response = client.get('/releng/releases/json/')
    assert response.status_code == 200


def test_json(db, client):
    response = client.get('/releng/releases/json/')
    assert response.status_code == 200

    data = response.json()
    assert data['releases'] == []


def test_netboot_page(db, client):
    response = client.get('/releng/netboot/')
    assert response.status_code == 200


def test_netboot_config(db, client):
    response = client.get('/releng/netboot/archlinux.ipxe')
    assert response.status_code == 200


def test_release_torrent(client, release, torrent_data):
    response = client.get(f'/releng/releases/{release.version}/torrent/')
    assert response.status_code == 404

    release.torrent_data = torrent_data
    release.save()
    response = client.get(f'/releng/releases/{release.version}/torrent/')
    assert response.status_code == 200


def test_release_details(client, release):
    response = client.get(f'/releng/releases/{release.version}/')
    assert response.status_code == 200
    assert release.version in response.content.decode()

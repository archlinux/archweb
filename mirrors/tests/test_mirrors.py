from mirrors.models import MirrorUrl


def test_details_empty(db, client):
    response = client.get('/mirrors/nothing/')
    assert response.status_code == 404


def test_details(db, client, mirrorurl):
    url = mirrorurl.mirror.get_absolute_url()

    response = client.get(url)
    assert response.status_code == 200


def test_details_json_empty(db, client):
    response = client.get('/mirrors/nothing/json/')
    assert response.status_code == 404


def test_details_json(db, client, mirrorurl):
    url = mirrorurl.mirror.get_absolute_url()

    response = client.get(url + 'json/')
    assert response.status_code == 200
    data = response.json()
    assert data['urls'] != []
    assert data['tier'] == 0
    assert 'upstream' not in data


def test_details_downstream_json(db, client, downstream_mirror, mirrorprotocol):
    mirror_url = MirrorUrl.objects.create(url="https://example.org/arch/mirror",
                                          protocol=mirrorprotocol,
                                          mirror=downstream_mirror,
                                          country="DE")

    url = mirror_url.mirror.get_absolute_url()
    response = client.get(url + 'json/')
    assert response.status_code == 200
    data = response.json()
    assert data['urls'] != []
    assert data['tier'] == 2
    assert data['upstream'] == 'mirror1'

    mirror_url.delete()


def test_url_details(db, client, mirrorurl):
    url = mirrorurl.mirror.get_absolute_url()
    response = client.get(url + f'{mirrorurl.id}/')
    assert response.status_code == 200

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


def test_url_details(db, client, mirrorurl):
    url = mirrorurl.mirror.get_absolute_url()
    response = client.get(url + '{}/'.format(mirrorurl.id))
    assert response.status_code == 200

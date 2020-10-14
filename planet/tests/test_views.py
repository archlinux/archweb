def test_feed(db, client):
    response = client.get('/feeds/planet/')
    assert response.status_code == 200


def test_planet(db, client):
    response = client.get('/planet/')
    assert response.status_code == 200

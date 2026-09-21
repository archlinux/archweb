def test_master_keys_empty(db, client):
    response = client.get('/api/v1/master-keys/')
    assert response.status_code == 200
    data = response.json()
    assert data['nodes'] == []
    assert data['edges'] == []


def test_master_keys_parity_with_legacy(db, client):
    v1 = client.get('/api/v1/master-keys/')
    legacy = client.get('/master-keys/json/')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()

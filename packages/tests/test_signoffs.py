def test_signoffs(client, developer_client):
    response = client.get('/packages/signoffs/')
    assert response.status_code == 200


def test_signoffs_json(client, developer_client):
    response = client.get('/packages/signoffs/json/')
    assert response.status_code == 200
    assert response.json()['signoff_groups'] == []

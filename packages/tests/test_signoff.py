def test_signoffs(admin_client, arches, repos, package):
    response = admin_client.get('/packages/signoffs/')
    assert response.status_code == 200


def test_signoffs_json(admin_client, arches, repos, package):
    response = admin_client.get('/packages/signoffs/json/')
    assert response.status_code == 200
    assert response.json()['signoff_groups'] == []

def test_releng_releases_json_deprecation_headers(db, client):
    response = client.get('/releng/releases/json/')
    assert response.status_code == 200
    assert response['Deprecation'] == 'true'
    assert response['Link'] == '</api/v1/releng/releases/>; rel="successor-version"'

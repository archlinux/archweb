"""OpenAPI schema contract tests for the Archweb API."""

def test_openapi_schema_served(client):
    response = client.get('/api/openapi.json')
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'


def test_openapi_schema_version(client):
    schema = client.get('/api/openapi.json').json()
    assert schema['openapi'].startswith('3.')
    assert schema['info']['title'] == 'Archweb API'
    assert schema['info']['version'] == '1'


def test_openapi_releng_releases_endpoint_present(client):
    paths = client.get('/api/openapi.json').json()['paths']
    assert '/api/v1/releng/releases/' in paths
    assert 'get' in paths['/api/v1/releng/releases/']


def test_openapi_releases_schema_fields(client):
    schema = client.get('/api/openapi.json').json()
    components = schema['components']['schemas']
    assert 'ReleasesSchema' in components
    assert 'ReleaseSchema' in components

    release_props = components['ReleaseSchema']['properties']
    required_fields = {'version', 'release_date', 'available', 'info'}
    assert required_fields <= release_props.keys()

    nullable_fields = {'kernel_version', 'md5_sum', 'sha1_sum', 'sha256_sum', 'b2_sum'}
    for field in nullable_fields:
        assert field in release_props
        types = {t.get('type') for t in release_props[field].get('anyOf', [])}
        assert 'null' in types, f"{field} must be nullable"


def test_openapi_docs_url_exists(client):
    response = client.get('/api/docs/')
    assert response.status_code == 200

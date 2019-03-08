def test_mirror_status(db, client):
        response = client.get('/mirrors/status/')
        assert response.status_code == 200


def test_json_endpoint(client, settings, mirrorurl):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    # Disables the cache_function's cache

    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    data = response.json()

    assert len(data['urls']) == 1
    mirror = data['urls'][0]
    assert mirror['url'] == mirrorurl.url


def test_json_endpoint_empty(db, client, settings):
    # Disables the cache_function's cache
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['urls'] == []


def test_json_tier_not_found(db, client, settings):
    response = client.get('/mirrors/status/tier/99/json/')
    assert response.status_code == 404


def test_json_tier_empty_cache(db, client, settings):
    response = client.get('/mirrors/status/tier/1/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['urls'] == []


def test_json_tier(client, settings, mirrorurl):
    # Disables the cache_function's cache
    settings.CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['urls'] != []

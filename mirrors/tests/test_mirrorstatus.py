import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


def test_mirror_status(db, client, create_mirrorlog):
    response = client.get('/mirrors/status/')
    assert response.status_code == 200

    check_time = datetime.now().replace(minute=0).replace(second=0).replace(microsecond=0)
    last_sync = check_time - timedelta(hours=128)
    duration = 10.0
    mirrorlog = create_mirrorlog(check_time, last_sync, duration)
    response = client.get('/mirrors/status/')

    # HACK: parsing HTML is annoying with elementtree
    data = response.content.decode()
    body_start = data.find('<table id="outofsync_mirrors"')
    body_end = data.find('</table>', body_start)
    tree = ET.fromstring(data[body_start:body_end + len('</table>')])
    for td in tree.find('tbody').find('tr').findall('td'):
        if td.find('a') is not None:
            mirrorurl = td.find('a').get('href')
            assert mirrorlog.url.get_absolute_url() == mirrorurl

    assert response.status_code == 200


def test_json_endpoint(client, settings, mirrorurl, create_mirrorlog):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    # Disables the cache_function's cache

    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    data = response.json()

    assert len(data['urls']) == 1
    assert data['num_checks'] == 0
    mirror = data['urls'][0]
    assert mirror['url'] == mirrorurl.url

    # out of sync mirror by 128 hours
    check_time = datetime.now().replace(minute=0).replace(second=0).replace(microsecond=0)
    last_sync = check_time - timedelta(hours=128)
    duration = 10.0
    create_mirrorlog(check_time, last_sync, duration)
    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    data = response.json()
    mirror = data['urls'][0]
    assert data['num_checks'] == 1
    assert mirror['delay'] > data['cutoff']
    assert mirror['duration_avg'] == duration
    assert mirror['last_sync'] == last_sync.isoformat()
    assert mirror['score'] > 1


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
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

    response = client.get('/mirrors/status/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['urls'] != []

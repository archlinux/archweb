import pytest


@pytest.mark.parametrize('url,expected', [
    ('/api/v1/mirrors/status/', ['max-age=311']),
    ('/api/v1/mirrors/status/tier/1/', ['max-age=311']),
    ('/api/v1/mirrors/locations/', ['max-age=317']),
    ('/api/v1/packages/pkgbase-maintainer', ['public', 'max-age=300']),
    ('/api/v1/master-keys/', ['max-age=1789']),
])
def test_cache_control(db, client, url, expected):
    response = client.get(url)
    assert response.status_code == 200
    cache_control = response.headers['Cache-Control']
    for part in expected:
        assert part in cache_control

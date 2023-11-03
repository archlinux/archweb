from mirrors.models import Mirror

# TODO(jelle): add test for https/rsync mirrors


def test_mirrorlist(client, mirrorurl):
    response = client.get('/mirrorlist/')
    assert response.status_code == 200


def test_mirrorlist_tier_last(client, mirrorurl):
    last_tier = Mirror.TIER_CHOICES[-1][0]
    response = client.get(f'/mirrorlist/tier/{last_tier + 1}/')
    assert response.status_code == 404


def test_mirrorlist_all(client, mirrorurl):
    response = client.get('/mirrorlist/all/')
    assert response.status_code == 200
    assert mirrorurl.hostname in response.content.decode()


def test_mirrorlist_all_https(client, mirrorurl):
    response = client.get('/mirrorlist/all/https/')
    assert response.status_code == 200
    assert mirrorurl.hostname in response.content.decode()


def test_mirrorlist_all_http(client, mirrorurl):
    # First test that without any http mirrors, we get a 404.
    response = client.get('/mirrorlist/all/http/')
    assert response.status_code == 404


def test_mirrorlist_status(client, mirrorurl):
    response = client.get('/mirrorlist/?country=all&use_mirror_status=on')
    assert response.status_code == 200


def test_mirrorlist_filter(client, create_mirrorurl):
    mirror1 = create_mirrorurl('JP', 'https://jp.org')
    mirror2 = create_mirrorurl()

    # First test that we correctly see the above mirror.
    response = client.get('/mirrorlist/?country=JP&protocol=https')
    assert response.status_code == 200
    assert mirror1.hostname in response.content.decode()

    # Now confirm that the US mirror did not show up.
    assert mirror2.hostname not in response.content.decode()

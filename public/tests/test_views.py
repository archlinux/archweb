def test_index(client, arches, repos, package, groups, staff_groups):
    response = client.get('/')
    assert response.status_code == 200


def test_index_logged_in(admin_client, arches, repos, package, groups, staff_groups):
    response = admin_client.get('/')
    assert response.status_code == 200


def test_about(client, arches, repos, package, groups, staff_groups):
    response = client.get('/about/')
    assert response.status_code == 200


def test_art(client, arches, repos, package, groups, staff_groups):
    response = client.get('/art/')
    assert response.status_code == 200


def test_svn(client, arches, repos, package, groups, staff_groups):
    response = client.get('/svn/')
    assert response.status_code == 200


def test_donate(client, arches, repos, package, groups, staff_groups):
    response = client.get('/donate/')
    assert response.status_code == 200


def test_download(client, arches, repos, package, groups, staff_groups):
    response = client.get('/download/')
    assert response.status_code == 200


def test_master_keys(client, arches, repos, package, groups, staff_groups):
    response = client.get('/master-keys/')
    assert response.status_code == 200


def test_master_keys_json(client, arches, repos, package, groups, staff_groups):
    response = client.get('/master-keys/json/')
    assert response.status_code == 200


def test_feeds(client, arches, repos, package, groups, staff_groups):
    response = client.get('/feeds/')
    assert response.status_code == 200


def test_people(client, arches, repos, package, groups, staff_groups):
    response = client.get('/people/developers/')
    assert response.status_code == 200


def test_sitemap(client, arches, repos, package, groups, staff_groups):
    sitemaps = ['sitemap', 'sitemap-base']
    for sitemap in sitemaps:
        response = client.get('/{}.xml'.format(sitemap))
        assert response.status_code == 200

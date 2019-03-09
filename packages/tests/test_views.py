def test_feed(db, client):
    response = client.get('/feeds/packages/')
    assert response.status_code == 200


def test_sitemap(db, client):
    for sitemap in ['packages', 'package-groups', 'package-files', 'split-packages']:
        response = client.get('/sitemap-{}.xml'.format(sitemap))
        assert response.status_code == 200


def test_arch_differences(client, arches, repos, package):
    response = client.get('/packages/differences/')
    assert response.status_code == 200

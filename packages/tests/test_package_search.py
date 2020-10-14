def test_invalid(client, arches, repos, package):
    response = client.get('/packages/?q=test')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_exact_match(client, arches, repos, package):
    response = client.get('/packages/?q=linux')
    assert response.status_code == 200
    assert '1 matching package found' in response.content.decode()


def test_filter_name(client, arches, repos, package):
    response = client.get('/packages/?name=name')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_filter_repo(client, arches, repos, package):
    response = client.get('/packages/?repo=Core')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_filter_desc(client, arches, repos, package):
    response = client.get('/packages/?desc=kernel')
    assert response.status_code == 200
    assert '1 matching package found' in response.content.decode()


def test_filter_flagged(client, arches, repos, package):
    response = client.get('/packages/?flagged=Flagged')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_filter_not_flagged(client, arches, repos, package):
    response = client.get('/packages/?flagged=Not Flagged')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_filter_arch(client, arches, repos, package):
    response = client.get('/packages/?arch=any')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_filter_maintainer_orphan(client, arches, repos, package):
    response = client.get('/packages/?maintainer=orphan')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_filter_packager_unknown(client, arches, repos, package):
    response = client.get('/packages/?packager=unknown')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_sort(client, arches, repos, package):
    response = client.get('/packages/?sort=pkgname')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_head(client, arches, repos, package):
    response = client.head('/packages/?q=unknown')
    assert response.status_code == 200

def test_invalid(client, db):
    response = client.get('/packages/?q=test')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_exact_match(client, package):
    response = client.get('/packages/?q=linux')
    assert response.status_code == 200
    assert '1 matching package found' in response.content.decode()


def test_filter_name(client, package):
    response = client.get('/packages/?name=name')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_filter_repo(client, package):
    response = client.get('/packages/?repo=Core')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_filter_desc(client, package):
    response = client.get('/packages/?desc=kernel')
    assert response.status_code == 200
    assert '1 matching package found' in response.content.decode()


def test_filter_flagged(client, package):
    response = client.get('/packages/?flagged=Flagged')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_filter_not_flagged(client, package):
    response = client.get('/packages/?flagged=Not Flagged')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_filter_arch(client, package):
    response = client.get('/packages/?arch=any')
    assert response.status_code == 200
    assert '0 matching packages found' in response.content.decode()


def test_filter_maintainer_orphan(client, package):
    response = client.get('/packages/?maintainer=orphan')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_filter_packager_unknown(client, package):
    response = client.get('/packages/?packager=unknown')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_sort(client, package):
    response = client.get('/packages/?sort=pkgname')
    assert response.status_code == 200
    assert '5 matching packages found' in response.content.decode()


def test_packages(client, package):
    response = client.get('/opensearch/packages/')
    assert response.status_code == 200
    assert 'template="http://example.com/opensearch/packages/"' in response.content.decode()


def test_packages_suggest(client, package):
    response = client.get('/opensearch/packages/suggest')
    assert response.status_code == 200


def test_packages_suggest_lowercase(client, package):
    response = client.get('/opensearch/packages/suggest?q=linux')
    assert response.status_code == 200
    assert 'linux' in response.content.decode()


def test_packages_suggest_uppercase(client, package):
    response = client.get('/opensearch/packages/suggest?q=LINUX')
    assert response.status_code == 200
    assert 'linux' in response.content.decode()

    response = client.get('/opensearch/packages/suggest?q=LINux')
    assert response.status_code == 200
    assert 'linux' in response.content.decode()


def test_group_search(client, package):
    response = client.get('/groups/search/json/?name=base-devel')
    assert response.status_code == 200

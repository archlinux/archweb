def test_packages(client, arches, repos, package):
    response = client.get('/opensearch/packages/')
    assert response.status_code == 200


def test_packages_suggest(client, arches, repos, package):
    response = client.get('/opensearch/packages/suggest')
    assert response.status_code == 200


def test_packages_suggest_lowercase(client, arches, repos, package):
    response = client.get('/opensearch/packages/suggest?q=linux')
    assert response.status_code == 200
    assert 'linux' in response.content.decode()


def test_packages_suggest_uppercase(client, arches, repos, package):
    response = client.get('/opensearch/packages/suggest?q=LINUX')
    assert response.status_code == 200
    assert 'linux' in response.content.decode()

    response = client.get('/opensearch/packages/suggest?q=LINux')
    assert response.status_code == 200
    assert 'linux' in response.content.decode()

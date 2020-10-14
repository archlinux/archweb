def test_invalid(client, arches, repos, package):
    response = client.get('/packages/search/json/')
    assert response.status_code == 200
    data = response.json()
    assert data['limit'] == 250
    assert data['results'] == []
    assert data['valid'] == False


def test_reponame(client, arches, repos, package):
    response = client.get('/packages/search/json/?repository=core')
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 5
    assert set([r['pkgname'] for r in data['results']]) == {"coreutils", "glibc", "linux", "pacman", "systemd"}

def test_packagename(client, arches, repos, package):
    response = client.get('/packages/search/json/?name=linux')
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 1


def test_no_results(client, arches, repos, package):
    response = client.get('/packages/search/json/?name=none')
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 0


def test_limit_four(client, arches, repos, package):
    response = client.get('/packages/search/json/?limit=4')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['num_pages'] == 2
    assert data['limit'] == 4
    assert len(data['results']) == 4


def test_second_page(client, arches, repos, package):
    response = client.get('/packages/search/json/?limit=4&page=2')
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 2
    assert data['num_pages'] == 2
    assert len(data['results']) == 1

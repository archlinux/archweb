from todolists.tests.conftest import (  # noqa: F401
    todolist,
    todolistpackage,
)


def test_todolist_not_found(db, client):
    response = client.get('/api/v1/todo/does-not-exist/')
    assert response.status_code == 404


def test_todolist_parity(db, client, todolist):  # noqa: F811
    v1 = client.get(f'/api/v1/todo/{todolist.slug}/')
    legacy = client.get(f'/todo/{todolist.slug}/json')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    assert v1.json() == legacy.json()


def test_todolist_with_package_parity(db, client, todolistpackage):  # noqa: F811
    slug = todolistpackage.todolist.slug
    v1 = client.get(f'/api/v1/todo/{slug}/')
    legacy = client.get(f'/todo/{slug}/json')
    assert v1.status_code == 200
    assert legacy.status_code == 200
    body = v1.json()
    assert len(body['packages']) == 1
    assert 'status_str' in body['packages'][0]
    assert body == legacy.json()

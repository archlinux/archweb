from todolists.models import Todolist, TodolistPackage


def assert_create_todo(client):
    response = client.post('/todo/add/', {
        'name': 'Foo rebuild',
        'description': 'The Foo Rebuild, please read the instructions',
        'raw': 'linux',
        'kind': Todolist.KIND_CHOICES[0][0],  # rebuild
    }, follow=True)
    assert response.status_code == 200


def test_todolist_overview(developer_client, todolist):
    response = developer_client.get('/todo/')
    assert response.status_code == 200
    assert todolist.name in response.content.decode()


def test_todolist_detail(todolist, developer_client):
    response = developer_client.get(todolist.get_absolute_url())
    assert response.status_code == 200
    assert todolist.name in response.content.decode()


def test_todolist_json(todolist, developer_client):
    response = developer_client.get(todolist.get_absolute_url() + 'json')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == todolist.name


def test_create_todolist(developer_client):
    assert_create_todo(developer_client)
    assert Todolist.objects.count() == 1
    Todolist.objects.all().delete()


def test_flag_pkg(developer_client, arches, repos, package):
    assert_create_todo(developer_client)

    todolist = Todolist.objects.first()
    package = todolist.packages().first()
    assert package.status == TodolistPackage.INCOMPLETE
    flag_url = f'/todo/{todolist.slug}/flag/{package.id}/'

    response = developer_client.get(flag_url)
    assert response.status_code == 302

    package = todolist.packages().first()
    assert package.status == TodolistPackage.COMPLETE

    # Flag incomplete again
    response = developer_client.get(flag_url)
    assert response.status_code == 302
    package = todolist.packages().first()
    assert package.status == TodolistPackage.INCOMPLETE

    # Test flagging from JS
    response = developer_client.get(flag_url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    data = response.json()
    assert data['status']
    assert data['css_class']

    Todolist.objects.all().delete()


def test_edit(developer_client, arches, repos, package):
    assert_create_todo(developer_client)

    todolist = Todolist.objects.first()
    assert todolist.packages().count() == 1

    response = developer_client.post(f'/todo/{todolist.slug}/edit/', {
        'name': 'Foo rebuild',
        'description': 'The Foo Rebuild, please read the instructions',
        'raw': 'linux\nglibc',
        'kind': Todolist.KIND_CHOICES[0][0],  # rebuild
    })
    assert response.status_code == 302
    todolist = Todolist.objects.first()
    assert todolist.packages().count() == 2

    Todolist.objects.all().delete()


def test_delete(developer_client, todolist):
    response = developer_client.post(f'/todo/{todolist.slug}/delete')
    assert response.status_code == 301


def test_json_endpoint(developer_client, todolist):
    response = developer_client.post(f'/todo/{todolist.slug}/json')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == todolist.name


def test_add_view(developer_client):
    response = developer_client.post('/todo/add/')
    assert response.status_code == 200


def test_edit_view(developer_client, todolist):
    response = developer_client.get(f'/todo/{todolist.slug}/edit/')
    assert response.status_code == 200

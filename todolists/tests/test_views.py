from todolists.models import Todolist, TodolistPackage


def assert_create_todo(client):
    response = client.post('/todo/add/', {
        'name': 'Foo rebuild',
        'description': 'The Foo Rebuild, please read the instructions',
        'raw': 'linux',
    }, follow=True)
    assert response.status_code == 200


def test_todolist_overview(user_client, todolist):
    response = user_client.get('/todo/')
    assert response.status_code == 200
    assert todolist.name in response.content.decode()


def test_todolist_detail(todolist, user_client):
    response = user_client.get(todolist.get_absolute_url())
    assert response.status_code == 200
    assert todolist.name in response.content.decode()


def test_todolist_json(todolist, user_client):
    response = user_client.get(todolist.get_absolute_url() + 'json')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == todolist.name


def test_create_todolist(user_client):
    assert_create_todo(user_client)
    assert Todolist.objects.count() == 1
    Todolist.objects.all().delete()


def test_flag_pkg(user_client, arches, repos, package):
    assert_create_todo(user_client)

    todolist = Todolist.objects.first()
    package = todolist.packages().first()
    assert package.status == TodolistPackage.INCOMPLETE

    response = user_client.get('/todo/{}/flag/{}/'.format(todolist.slug, package.id))
    assert response.status_code == 302

    package = todolist.packages().first()
    assert package.status == TodolistPackage.COMPLETE

    Todolist.objects.all().delete()

def test_edit(user_client, arches, repos, package):
    assert_create_todo(user_client)

    todolist = Todolist.objects.first()
    assert todolist.packages().count() == 1

    response = user_client.post('/todo/{}/edit/'.format(todolist.slug), {
        'name': 'Foo rebuild',
        'description': 'The Foo Rebuild, please read the instructions',
        'raw': 'linux\nglibc',
    })
    assert response.status_code == 302
    todolist = Todolist.objects.first()
    assert todolist.packages().count() == 2

    Todolist.objects.all().delete()

def test_delete(user_client, arches, repos, package):
    assert_create_todo(user_client)

    todolist = Todolist.objects.first()
    response = user_client.post('/todo/{}/delete'.format(todolist.slug))
    assert response.status_code == 301
    Todolist.objects.all().delete()

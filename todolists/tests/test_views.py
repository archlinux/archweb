from django.contrib.auth.models import User
from django.test import TestCase


from todolists.models import Todolist, TodolistPackage


class TestTodolist(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        self.user = User.objects.create(username="joeuser", first_name="Joe",
                                        last_name="User", email="user1@example.com")
        self.todolist = Todolist.objects.create(name='Boost rebuild',
                                                description='Boost 1.66 rebuid',
                                                creator=self.user,
                                                slug='boost-rebuild',
                                                raw='linux')

    def test_todolist_overview(self):
        response = self.client.get('/todo/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.todolist.name, response.content.decode())

    def test_todolist_detail(self):
        response = self.client.get(self.todolist.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.todolist.name, response.content.decode())

    def test_todolist_json(self):
        response = self.client.get(self.todolist.get_absolute_url() + 'json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], self.todolist.name)


class TestTodolistAdmin(TestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json',
                'main/fixtures/package.json']

    def setUp(self):
        password = 'test'
        self.user = User.objects.create_superuser("admin",
                                                  "admin@archlinux.org",
                                                  password)

        self.client.post('/login/', {
                                    'username': self.user.username,
                                    'password': password
        })

    def tearDown(self):
        Todolist.objects.all().delete()
        self.user.delete()

    def create_todo(self):
        return self.client.post('/todo/add/', {
            'name': 'Foo rebuild',
            'description': 'The Foo Rebuild, please read the instructions',
            'raw': 'linux',
        })

    def test_create_todolist(self):
        response = self.create_todo()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Todolist.objects.all()), 1)

    def test_flag_pkg(self):
        response = self.create_todo()
        self.assertEqual(response.status_code, 302)

        todolist = Todolist.objects.first()
        package = todolist.packages().first()
        self.assertEqual(package.status, TodolistPackage.INCOMPLETE)

        response = self.client.get('/todo/{}/flag/{}/'.format(todolist.slug, package.id))
        self.assertEqual(response.status_code, 302)

        package = todolist.packages().first()
        self.assertEqual(package.status, TodolistPackage.COMPLETE)

    def test_edit(self):
        response = self.create_todo()
        self.assertEqual(response.status_code, 302)
        todolist = Todolist.objects.first()
        self.assertEqual(len(todolist.packages().all()), 1)

        response = self.client.post('/todo/{}/edit/'.format(todolist.slug), {
            'name': 'Foo rebuild',
            'description': 'The Foo Rebuild, please read the instructions',
            'raw': 'linux\nglibc',
        })
        self.assertEqual(response.status_code, 302)
        todolist = Todolist.objects.first()
        self.assertEqual(len(todolist.packages().all()), 2)

    def test_delete(self):
        response = self.create_todo()
        self.assertEqual(response.status_code, 302)
        todolist = Todolist.objects.first()
        response = self.client.post('/todo/{}/delete'.format(todolist.slug))
        self.assertEqual(response.status_code, 301)

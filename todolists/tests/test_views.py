from django.contrib.auth.models import User
from django.test import TestCase


from todolists.models import Todolist


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

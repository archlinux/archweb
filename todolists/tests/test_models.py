from django.contrib.auth.models import User
from django.test import TestCase


from main.models import Package
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
                                                raw='linux')

    def tearDown(self):
        self.todolist.delete()
        self.user.delete()

    def test_stripped_description(self):
        self.todolist.description = 'Boost rebuild '
        desc = self.todolist.stripped_description
        self.assertFalse(desc.endswith(' '))

    def test_get_absolute_url(self):
        self.assertIn('/todo/', self.todolist.get_absolute_url())

    def test_get_full_url(self):
        url = self.todolist.get_full_url()
        self.assertIn('https://example.com/todo/', url)

    def test_packages(self):
        pkg = Package.objects.first()
        todopkg = TodolistPackage.objects.create(pkg=pkg, pkgname=pkg.pkgname,
                                                 pkgbase=pkg.pkgbase, arch=pkg.arch,
                                                 repo=pkg.repo, user=self.user,
                                                 todolist=self.todolist)
        pkgs = self.todolist.packages()
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0], todopkg)

from django.contrib.auth.models import User
from django.test import TestCase


from main.models import Package
from todolists.models import Todolist, TodolistPackage
from todolists.templatetags.todolists import todopkg_details_link


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

    def test_details_link(self):
        pkg = Package.objects.first()
        todopkg = TodolistPackage.objects.create(pkg=pkg, pkgname=pkg.pkgname,
                                                 pkgbase=pkg.pkgbase, arch=pkg.arch,
                                                 repo=pkg.repo, user=self.user,
                                                 todolist=self.todolist)
        link = todopkg_details_link(todopkg)
        self.assertIn('View package details for {}'.format(todopkg.pkg.pkgname), link)

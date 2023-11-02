from main.models import Package
from todolists.models import TodolistPackage
from todolists.tests.conftest import NAME


def test_stripped_description(todolist):
    todolist.description = 'Boost rebuild '
    desc = todolist.stripped_description
    assert not desc.endswith(' ')


def test_get_absolute_url(todolist):
    assert '/todo/' in todolist.get_absolute_url()


def test_get_full_url(todolist):
    url = todolist.get_full_url()
    assert 'https://example.com/todo/' in url


def test_packages(admin_user, todolist, todolistpackage):
    pkgs = todolist.packages()
    assert len(pkgs) == 1
    assert pkgs[0] == todolistpackage


def test_str(admin_user, todolist):
    assert NAME in str(todolist)


def test_todolist_str(admin_user, todolist, todolistpackage):
    assert todolistpackage.pkgname in str(todolistpackage)


def test_status_css_class(admin_user, todolist, todolistpackage):
    assert todolistpackage.status_css_class() == 'incomplete'


def test_status_str(admin_user, todolist, todolistpackage):
    assert todolistpackage.status_str == 'Incomplete'


def test_todolist_complete(admin_user, todolist, todolistpackage, mailoutbox):
    pkg = Package.objects.last()
    todopkg = TodolistPackage.objects.create(pkg=pkg, pkgname=pkg.pkgname,
                                             pkgbase=pkg.pkgbase, arch=pkg.arch,
                                             repo=pkg.repo, user=admin_user,
                                             todolist=todolist,
                                             status=TodolistPackage.COMPLETE)
    assert todopkg
    assert len(mailoutbox) == 0
    todolistpackage.status = TodolistPackage.COMPLETE
    todolistpackage.save()
    assert len(mailoutbox) == 1
    todopkg.delete()

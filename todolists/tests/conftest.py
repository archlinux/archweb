import pytest

from main.models import Package
from todolists.models import Todolist, TodolistPackage


NAME = 'Boost rebuild'
SLUG = 'boost-rebuild'
DESCRIPTION = 'Boost 1.66 rebuild'
RAW = 'linux'


@pytest.fixture
def todolist(admin_user, arches, repos, package):
    todolist = Todolist.objects.create(name=NAME,
                                       description=DESCRIPTION,
                                       slug=SLUG,
                                       creator=admin_user,
                                       raw=RAW)
    yield todolist
    todolist.delete()


@pytest.fixture
def todolistpackage(admin_user, todolist):
    pkg = Package.objects.first()
    todopkg = TodolistPackage.objects.create(pkg=pkg, pkgname=pkg.pkgname,
                                             pkgbase=pkg.pkgbase, arch=pkg.arch,
                                             repo=pkg.repo, user=admin_user,
                                             todolist=todolist)
    yield todopkg
    todopkg.delete()

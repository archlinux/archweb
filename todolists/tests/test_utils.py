import pytest
from django.utils.timezone import now

from main.models import Package, Repo
from todolists.models import TodolistPackage
from todolists.utils import attach_staging, attach_testing


def make_package(pkgname, repo, arch):
    return Package.objects.create(
        pkgname=pkgname,
        pkgbase=pkgname,
        pkgver='1.0',
        pkgrel='1',
        epoch=0,
        pkgdesc='Test package',
        url='https://example.com',
        filename=f'{pkgname}-1.0-1-x86_64.pkg.tar.zst',
        compressed_size=1000,
        installed_size=2000,
        build_date=now(),
        last_update=now(),
        created=now(),
        packager_str='Test Packager',
        repo=repo,
        arch=arch,
    )


@pytest.fixture
def stable_pkg(repos, package):
    return Package.objects.get(pkgname='linux')


@pytest.fixture
def todolist_with_linux(todolist, stable_pkg, user):
    arch = stable_pkg.arch
    repo = stable_pkg.repo
    tlpkg = TodolistPackage.objects.create(
        todolist=todolist,
        pkg=stable_pkg,
        pkgname=stable_pkg.pkgname,
        pkgbase=stable_pkg.pkgbase,
        arch=arch,
        repo=repo,
        user=user,
    )
    yield todolist
    tlpkg.delete()


def test_attach_testing_no_testing_pkg(todolist_with_linux):
    todolist = todolist_with_linux
    attach_testing(todolist.packages(), todolist.pk)
    for pkg in todolist.packages():
        assert pkg.testing is None


def test_attach_testing_finds_testing_pkg(todolist_with_linux):
    todolist = todolist_with_linux
    stable_pkg = Package.objects.get(pkgname='linux', repo__testing=False, repo__staging=False)
    testing_repo = Repo.objects.get(name='Core-Testing')

    testing_pkg = make_package('linux', testing_repo, stable_pkg.arch)
    try:
        attach_testing(todolist.packages(), todolist.pk)
        for pkg in todolist.packages():
            if pkg.pkgname == 'linux':
                assert pkg.testing is not None
                assert pkg.testing.repo.testing is True
    finally:
        testing_pkg.delete()


def test_attach_testing_ignores_staging_repos(todolist_with_linux):
    todolist = todolist_with_linux
    stable_pkg = Package.objects.get(pkgname='linux', repo__testing=False, repo__staging=False)
    staging_repo = Repo.objects.get(name='Core-Staging')

    staging_pkg = make_package('linux', staging_repo, stable_pkg.arch)
    try:
        attach_testing(todolist.packages(), todolist.pk)
        for pkg in todolist.packages():
            if pkg.pkgname == 'linux':
                assert pkg.testing is None
    finally:
        staging_pkg.delete()


def test_attach_staging_still_works(todolist_with_linux):
    todolist = todolist_with_linux
    stable_pkg = Package.objects.get(pkgname='linux', repo__testing=False, repo__staging=False)
    staging_repo = Repo.objects.get(name='Core-Staging')

    staging_pkg = make_package('linux', staging_repo, stable_pkg.arch)
    try:
        attach_staging(todolist.packages(), todolist.pk)
        for pkg in todolist.packages():
            if pkg.pkgname == 'linux':
                assert pkg.staging is not None
                assert pkg.staging.repo.staging is True
    finally:
        staging_pkg.delete()

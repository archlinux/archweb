import pytest

from todolists.models import Todolist, TodolistPackage
from todolists.tests.conftest import NAME


@pytest.fixture
def other_todolist(user, todolistpackage):
    other = Todolist.objects.create(name='Other rebuild', description='Other rebuild',
                                    slug='other-rebuild', creator=user,
                                    stages=Todolist.DEFAULT_STAGES[Todolist.REBUILD])
    TodolistPackage.objects.create(todolist=other, pkg=todolistpackage.pkg,
                                   pkgname=todolistpackage.pkgname,
                                   pkgbase=todolistpackage.pkgbase,
                                   arch=todolistpackage.arch, repo=todolistpackage.repo)
    yield other
    other.delete()


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


def test_stages(todolist):
    assert [stage.name for stage in todolist.stage_list] == [
        'Draft', 'Rebuild in staging', 'Test in testing']
    assert todolist.current_stage.key == 'draft'
    assert not todolist.finished

    todolist.progress = 3
    assert todolist.current_stage is None
    assert todolist.finished


def test_per_package_reached(todolist):
    assert not todolist.per_package_reached()
    todolist.progress = 1
    assert todolist.per_package_reached()
    todolist.progress = 2
    assert todolist.per_package_reached()


def test_package_complete(todolist, todolistpackage):
    todolist.progress = 1
    todolist.save()
    todolistpackage.progress = 1
    assert not todolistpackage.is_complete
    todolistpackage.progress = 2
    assert todolistpackage.is_complete
    assert todolistpackage.status_str == 'Complete'


def test_package_complete_finished_list(todolist, todolistpackage):
    todolist.progress = 3
    todolist.save()
    todolistpackage.progress = 3
    assert todolistpackage.is_complete


def test_can_advance(todolist, todolistpackage):
    # draft does not ask for per-package completion
    assert todolist.can_advance()

    todolist.progress = 1
    todolistpackage.progress = 1
    todolistpackage.save()
    assert not todolist.can_advance()

    todolistpackage.progress = 2
    todolistpackage.save()
    assert todolist.can_advance()

    todolist.progress = 3
    assert not todolist.can_advance()


def test_can_advance_ignores_removed(todolist, todolistpackage):
    todolist.progress = 1
    todolistpackage.progress = 1
    todolistpackage.removed = todolistpackage.created
    todolistpackage.save()
    assert todolist.can_advance()


def test_missing_package_names(admin_user, todolist, todolistpackage):
    todolist.raw = f'{todolistpackage.pkgname}\r\nnonexistent\n\n nonexistent \nother\n'
    assert todolist.missing_package_names() == ['nonexistent', 'other']


def test_missing_package_names_none(admin_user, todolist, todolistpackage):
    todolist.raw = todolistpackage.pkgname
    assert todolist.missing_package_names() == []


def test_overlapping_rebuilds(todolist, todolistpackage, other_todolist):
    assert todolist.overlapping_rebuilds() == [(other_todolist, [todolistpackage.pkgbase])]
    assert other_todolist.overlapping_rebuilds() == [(todolist, [todolistpackage.pkgbase])]


def test_overlapping_rebuilds_finished(todolist, todolistpackage, other_todolist):
    other_todolist.progress = 3
    other_todolist.save()
    assert todolist.overlapping_rebuilds() == []
    # finished lists do not show the warning themselves
    assert other_todolist.overlapping_rebuilds() == []


def test_overlapping_rebuilds_task(todolist, todolistpackage, other_todolist):
    other_todolist.kind = Todolist.TASK
    other_todolist.save()
    assert todolist.overlapping_rebuilds() == []
    assert other_todolist.overlapping_rebuilds() == []


def test_overlapping_rebuilds_removed(todolist, todolistpackage, other_todolist):
    todolistpackage.removed = todolistpackage.created
    todolistpackage.save()
    assert todolist.overlapping_rebuilds() == []
    assert other_todolist.overlapping_rebuilds() == []


def test_overlapping_rebuilds_none(todolist, todolistpackage):
    assert todolist.overlapping_rebuilds() == []

from todolists.tests.conftest import NAME, RAW


def test_stripped_description(todolist):
    todolist.description = 'Boost rebuild '
    desc = todolist.stripped_description
    assert desc.endswith(' ') == False


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

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

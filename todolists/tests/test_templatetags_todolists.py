from todolists.templatetags.todolists import todopkg_details_link


def test_details_link(todolistpackage):
    link = todopkg_details_link(todolistpackage)
    assert f'View package details for {todolistpackage.pkg.pkgname}' in link

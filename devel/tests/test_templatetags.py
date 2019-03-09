from devel.templatetags.group import in_group


def test_in_group(admin_user):
    assert in_group(admin_user, 'none') == False

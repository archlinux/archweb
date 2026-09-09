from django.contrib.auth.models import User

from devel.templatetags.group import in_group


def test_in_group(db):
    user = User.objects.create(username="joeuser", first_name="Joe",
                               last_name="User", email="user1@example.com")
    assert in_group(user, 'none') is False
    user.delete()

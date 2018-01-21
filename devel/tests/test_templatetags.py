from django.contrib.auth.models import User
from django.test import SimpleTestCase

from devel.templatetags.group import in_group


class DevelTemplatetagsTest(SimpleTestCase):
    def test_in_group(self):
        user = User.objects.create(username="joeuser", first_name="Joe",
                                   last_name="User", email="user1@example.com")
        self.assertEqual(in_group(user, 'none'), False)


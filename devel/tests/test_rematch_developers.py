from mock import patch


from django.core.management import call_command
from django.test import TransactionTestCase


class RepoReadTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def test_rematch_developers(self):
        with patch('devel.management.commands.rematch_developers.logger') as logger:
            call_command('rematch_developers')
        logger.info.assert_called()

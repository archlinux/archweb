from unittest.mock import Mock


from django.core.management import call_command
from django.test import TransactionTestCase


class RematchDeveloperTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def test_rematch_developers(self):
        logger = Mock()
        call_command('rematch_developers', logger=logger)
        logger.info.assert_called()

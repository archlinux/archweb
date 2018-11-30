from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase


class PGPImportTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def test_pgp_import(self):
        with self.assertRaises(CommandError) as e:
            call_command('pgp_import')
        self.assertIn('keyring_path', str(e.exception))

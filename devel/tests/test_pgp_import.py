from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase

CREATED = 1541685162
USER = 'John Doe <jdoe@archlinux.org>'
ID1 = 'D6C055F238843F1C'
ID2 = 'D8AFDDA07A5B6EDFA7D8CCDAD6D055F927843F1C'
ID3 = 'B588C0234ECADD3F0BBBEEBA44F9F02E089294E7'

SIG_DATA = [
    f'pub:-:4096:1:{ID1}:{CREATED}:::-:::scESCA::::::23::0:',
    f'fpr:::::::::{ID2}:',
    f'uid:-::::{CREATED}::{ID3}::{USER}::::::::::0:',
    f'sig:::1:{ID1}:{CREATED}::::{USER}:13x::{ID2}:::10:'
]


class PGPImportTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def test_pgp_import_error(self):
        with self.assertRaises(CommandError) as e:
            call_command('pgp_import')
        self.assertIn('keyring_path', str(e.exception))

    @patch('devel.management.commands.pgp_import.call_gpg')
    def test_pgp_import_garbage_data(self, mock_call_gpg):
        mock_call_gpg.return_value = 'barf'
        with patch('devel.management.commands.pgp_import.logger') as logger:
            call_command('pgp_import', '/tmp')
        logger.info.assert_called()
        logger.info.assert_any_call('created %d, updated %d signatures', 0, 0)
        logger.info.assert_any_call('created %d, updated %d keys', 0, 0)

    @patch('devel.management.commands.pgp_import.call_gpg')
    def test_pgp_import(self, mock_call_gpg):
        mock_call_gpg.return_value = '\n'.join(SIG_DATA)
        with patch('devel.management.commands.pgp_import.logger') as logger:
            call_command('pgp_import', '/tmp')
        logger.info.assert_called()
        logger.info.assert_any_call('created %d, updated %d signatures', 0, 0)
        logger.info.assert_any_call('created %d, updated %d keys', 1, 0)

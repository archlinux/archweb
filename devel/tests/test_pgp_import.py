from unittest.mock import patch

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


CREATED = 1541685162
USER = 'John Doe <jdoe@archlinux.org>'
ID1 = 'D6C055F238843F1C'
ID2 = 'D8AFDDA07A5B6EDFA7D8CCDAD6D055F927843F1C'
ID3 = 'B588C0234ECADD3F0BBBEEBA44F9F02E089294E7'

SIG_DATA = [
        'pub:-:4096:1:{id1}:{created}:::-:::scESCA::::::23::0:'.format(id1=ID1, created=CREATED),
        'fpr:::::::::{id2}:'.format(id2=ID2),
        'uid:-::::{created}::{id3}::{user}::::::::::0:'.format(created=CREATED, id3=ID3, user=USER),
        'sig:::1:{id1}:{created}::::{user}:13x::{id2}:::10:'.format(id1=ID1, created=CREATED, user=USER, id2=ID2)
]


def test_pgp_import_error(arches, repos):
    with pytest.raises(CommandError) as e:
        call_command('pgp_import')
    assert 'keyring_path' in str(e.value)


@patch('devel.management.commands.pgp_import.call_gpg')
def test_pgp_import_garbage_data(mock_call_gpg, arches, repos):
    mock_call_gpg.return_value = 'barf'
    with patch('devel.management.commands.pgp_import.logger') as logger:
        call_command('pgp_import', '/tmp')
    logger.info.assert_called()
    logger.info.assert_any_call('created %d, updated %d signatures', 0, 0)
    logger.info.assert_any_call('created %d, updated %d keys', 0, 0)

@patch('devel.management.commands.pgp_import.call_gpg')
def test_pgp_import(mock_call_gpg, arches, repos):
    mock_call_gpg.return_value = '\n'.join(SIG_DATA)
    with patch('devel.management.commands.pgp_import.logger') as logger:
        call_command('pgp_import', '/tmp')
    logger.info.assert_called()
    logger.info.assert_any_call('created %d, updated %d signatures', 0, 0)
    logger.info.assert_any_call('created %d, updated %d keys', 1, 0)

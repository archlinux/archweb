from unittest.mock import patch

from django.core.management import call_command


def test_rematch_developers(arches, repos):
    with patch('devel.management.commands.rematch_developers.logger') as logger:
        call_command('rematch_developers')
    logger.info.assert_called()

import tarfile
from mock import patch


from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase
from django.utils.six import StringIO


from main.models import Package


# Django's TestCase is wrapped in transaction, therefore use TransactionTestCase
class RepoReadTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def test_invalid_args(self):
        with self.assertRaises(CommandError) as e:
            call_command('reporead')
        self.assertIn('Architecture is required', str(e.exception))

        with self.assertRaises(CommandError) as e:
            call_command('reporead', 'x86_64')
        self.assertIn('Package database file is required.', str(e.exception))

        with self.assertRaises(CommandError) as e:
            call_command('reporead', 'x86_64', 'nothing.db.tar.gz')
        self.assertIn('Specified package database file does not exist.', str(e.exception))

    def test_read_packages(self):
        out = StringIO()
        with patch('devel.management.commands.reporead.logger') as logger:
            call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
        logger.info.assert_called()

        # Verify contents
        with tarfile.open('devel/fixtures/core.db.tar.gz') as tar:
            files = [name.replace('core.db/', '') for name in tar.getnames() if name != 'core.db' and not 'desc' in name]

        packages = Package.objects.all()
        import_packages = ["{}-{}-{}".format(pkg.pkgname, pkg.pkgver, pkg.pkgrel) for pkg in packages]
        self.assertItemsEqual(files, import_packages)

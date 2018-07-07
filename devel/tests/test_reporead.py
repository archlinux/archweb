import tarfile
from mock import patch
from datetime import datetime


from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase
from django.utils import timezone


from main.models import Arch, Package, Repo
from packages.models import FlagRequest


# Django's TestCase is wrapped in transaction, therefore use TransactionTestCase
class RepoReadTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def create_pkg(self, repo=None, pkgver='4.10.1', pkgrel='1'):
        if not repo:
            repo = Repo.objects.get(name__iexact='core')

        arch = Arch.objects.get(name__iexact='any')
        now = datetime.now(tz=timezone.utc)
        return Package.objects.create(arch=arch, repo=repo, pkgname='systemd',
                                     pkgbase='systemd', pkgver=pkgver,
                                     pkgrel=pkgrel, pkgdesc='Linux kernel',
                                     compressed_size=10, installed_size=20,
                                     last_update=now, created=now)

    def test_invalid_args(self):
        with self.assertRaises(CommandError) as e:
            call_command('reporead')
        self.assertIn('missing arch and file.', str(e.exception))

        with self.assertRaises(CommandError) as e:
            call_command('reporead', 'x86_64')
        self.assertIn('Package database file is required.', str(e.exception))

        with self.assertRaises(CommandError) as e:
            call_command('reporead', 'x86_64', 'nothing.db.tar.gz')
        self.assertIn('Specified package database file does not exist.', str(e.exception))

    def test_read_packages(self):
        with patch('devel.management.commands.reporead.logger') as logger:
            call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
        logger.info.assert_called()

        # Verify contents
        with tarfile.open('devel/fixtures/core.db.tar.gz') as tar:
            files = [name.replace('core.db/', '') for name in tar.getnames() if name != 'core.db' and not 'desc' in name]

        packages = Package.objects.all()
        import_packages = ["{}-{}-{}".format(pkg.pkgname, pkg.pkgver, pkg.pkgrel) for pkg in packages]
        self.assertItemsEqual(files, import_packages)

    def test_flagoutofdate(self):
        pkg = self.create_pkg()
        FlagRequest.objects.create(pkgbase=pkg.pkgbase, repo=pkg.repo,
                                   pkgver=pkg.pkgver, epoch=pkg.epoch,
                                   ip_address='1.1.1.1')

        with patch('devel.management.commands.reporead.logger') as logger:
            call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
        logger.info.assert_called()

        self.assertEqual(len(FlagRequest.objects.all()), 0)

    def test_flagoutofdate_staging(self):
        staging = Repo.objects.get(name__iexact='staging')

        pkg = self.create_pkg()
        staging_pkg = self.create_pkg(repo=staging, pkgrel='2')

        FlagRequest.objects.create(pkgbase=pkg.pkgbase, repo=pkg.repo,
                                   pkgver=pkg.pkgver, epoch=pkg.epoch,
                                   ip_address='1.1.1.1')
        FlagRequest.objects.create(pkgbase=staging_pkg.pkgbase, repo=staging_pkg.repo,
                                   pkgver=staging_pkg.pkgver, epoch=staging_pkg.epoch,
                                   ip_address='1.1.1.1')

        with patch('devel.management.commands.reporead.logger') as logger:
            call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
        logger.info.assert_called()

        objects =  FlagRequest.objects.all()
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].pkgver, staging_pkg.pkgver)

import tarfile
from unittest.mock import patch
from datetime import datetime

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone


from main.models import Arch, Package, Repo
from packages.models import FlagRequest


@pytest.fixture
def create_pkg(arches, repos):
    packages = []

    def _create_pkg(repo=None, pkgver='4.10.1', pkgrel='1'):
        if not repo:
            repo = Repo.objects.get(name__iexact='core')

        arch = Arch.objects.get(name__iexact='any')
        now = datetime.now(tz=timezone.utc)
        package = Package.objects.create(arch=arch, repo=repo, pkgname='systemd',
                                         pkgbase='systemd', pkgver=pkgver,
                                         pkgrel=pkgrel, pkgdesc='Linux kernel',
                                         compressed_size=10, installed_size=20,
                                         last_update=now, created=now)
        packages.append(package)
        return package

    yield _create_pkg

    for package in packages:
        package.delete()


def test_invalid_args():
    with pytest.raises(CommandError) as excinfo:
        call_command('reporead')
    assert 'missing arch and file.' in str(excinfo)

    with pytest.raises(CommandError) as excinfo:
        call_command('reporead', 'x86_64')
    assert 'Package database file is required.' in str(excinfo)

    with pytest.raises(CommandError) as excinfo:
        call_command('reporead', 'x86_64', 'nothing.db.tar.gz')
    assert 'Specified package database file does not exist.' in str(excinfo)


def test_invalid_arch(transactional_db, arches, repos):
    with pytest.raises(CommandError) as excinfo:
        call_command('reporead', 'armv64', 'devel/fixtures/core.db.tar.gz')
    assert 'Specified architecture armv64 is not currently known.' in str(excinfo)


# TODO: create pacman repo db with a pytest fixture
def test_read_packages(transactional_db, arches, repos):
    with patch('devel.management.commands.reporead.logger') as logger:
        call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
    logger.info.assert_called()

    # Verify contents
    with tarfile.open('devel/fixtures/core.db.tar.gz') as tar:
        files = [name.replace('core.db/', '') for name in tar.getnames() if name != 'core.db' and not 'desc' in name]

    packages = Package.objects.all()
    import_packages = ["{}-{}-{}".format(pkg.pkgname, pkg.pkgver, pkg.pkgrel) for pkg in packages]
    assert len(files) == len(import_packages)


def test_flagoutofdate(transactional_db, create_pkg):
    pkg = create_pkg()
    FlagRequest.objects.create(pkgbase=pkg.pkgbase, repo=pkg.repo,
                               pkgver=pkg.pkgver, epoch=pkg.epoch,
                               ip_address='1.1.1.1')

    with patch('devel.management.commands.reporead.logger') as logger:
        call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
    logger.info.assert_called()

    assert not len(FlagRequest.objects.all())


def test_flagoutofdate_staging(transactional_db, create_pkg):
    staging = Repo.objects.get(name__iexact='staging')

    pkg = create_pkg()
    staging_pkg = create_pkg(repo=staging, pkgrel='2')

    FlagRequest.objects.create(pkgbase=pkg.pkgbase, repo=pkg.repo,
                               pkgver=pkg.pkgver, epoch=pkg.epoch,
                               ip_address='1.1.1.1')
    FlagRequest.objects.create(pkgbase=staging_pkg.pkgbase, repo=staging_pkg.repo,
                               pkgver=staging_pkg.pkgver, epoch=staging_pkg.epoch,
                               ip_address='1.1.1.1')

    with patch('devel.management.commands.reporead.logger') as logger:
        call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
    logger.info.assert_called()

    objects = FlagRequest.objects.all()
    assert len(objects) == 1
    assert objects[0].pkgver == staging_pkg.pkgver

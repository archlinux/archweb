import tarfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

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
        return Package.objects.create(arch=arch, repo=repo, pkgname='systemd',
                                      pkgbase='systemd', pkgver=pkgver,
                                      pkgrel=pkgrel, pkgdesc='Linux kernel',
                                      compressed_size=10, installed_size=20,
                                      last_update=now, created=now)

    yield _create_pkg

    for pkg in packages:
        pkg.delete()


def test_invalid_arch(arches):
    with pytest.raises(CommandError) as exc_info:
        call_command('reporead', 'armv64', 'devel/fixtures/core.db.tar.gz')
    assert exc_info.value.args[0] == 'Specified architecture armv64 is not currently known.'


def test_invalid_args(arches):
    with pytest.raises(CommandError) as exc_info:
        call_command('reporead')
    assert 'missing arch and file' in str(exc_info)

    with pytest.raises(CommandError) as exc_info:
        call_command('reporead', 'x86_64')
    assert 'Package database file is required' in str(exc_info)

    with pytest.raises(CommandError) as exc_info:
        call_command('reporead', 'x86_64', 'nothing.db.tar.gz')
    assert 'Specified package database file does not exist.' in str(exc_info)


def test_read_packages(transactional_db, arches, repos):
    # TODO: use pytest-pacman for generating the database
    with patch('devel.management.commands.reporead.logger') as logger:
        call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
    logger.info.assert_called()

    # Verify contents
    with tarfile.open('devel/fixtures/core.db.tar.gz') as tar:
        files = [name.replace('core.db/', '') for name in tar.getnames()
                 if name != 'core.db' and 'desc' not in name]

    packages = Package.objects.all()
    import_packages = [f"{pkg.pkgname}-{pkg.pkgver}-{pkg.pkgrel}" for pkg in packages]
    assert len(files) == len(import_packages)


def test_flagoutofdate(transactional_db, arches, repos, create_pkg):
    pkg = create_pkg()
    FlagRequest.objects.create(pkgbase=pkg.pkgbase, repo=pkg.repo,
                               pkgver=pkg.pkgver, epoch=pkg.epoch,
                               ip_address='1.1.1.1')

    with patch('devel.management.commands.reporead.logger') as logger:
        call_command('reporead', 'x86_64', 'devel/fixtures/core.db.tar.gz')
    logger.info.assert_called()

    assert len(FlagRequest.objects.all()) == 0


def test_flagoutofdate_staging(transactional_db, arches, repos, create_pkg):
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

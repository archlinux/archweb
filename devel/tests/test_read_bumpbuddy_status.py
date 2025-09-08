from typing import TYPE_CHECKING

import pytest
from django.utils.timezone import now

from devel.management.commands.read_bumpbuddy_status import Command as BumpBuddyCommand
from main.models import Arch, Package, Repo
from packages.alpm import AlpmAPI

if TYPE_CHECKING:
    from packages.models import FlagRequest

alpm = AlpmAPI()


@pytest.fixture
def command():
    return BumpBuddyCommand()


@pytest.fixture
def package(arches, repos):
    arch = Arch.objects.get(name='x86_64')
    extra = Repo.objects.get(name='Extra')
    created = now()
    pkg = Package.objects.create(arch=arch, repo=extra,
                                 pkgname='systemd',
                                 pkgbase='systemd', pkgver=100,
                                 pkgrel=1, pkgdesc='Linux kernel',
                                 compressed_size=10, installed_size=20,
                                 last_update=created, created=created)

    yield pkg
    pkg.delete()


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_not_outofdate(command, package):
    request = command.process_package({
        'pkgbase': 'systemd',
        'local_version': 100,
        'upstream_version': 100,
        'out_of_date': False,
        'issue': 12
    })

    assert request is None


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_outofdate(command, package):
    request = command.process_package({
        'pkgbase': 'systemd',
        'local_version': 100,
        'upstream_version': 101,
        'out_of_date': True,
        'issue': 12
    })

    assert request is not None


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_already_flagged(command, package):
    request: FlagRequest = command.process_package({
        'pkgbase': 'systemd',
        'local_version': 100,
        'upstream_version': 101,
        'out_of_date': True,
        'issue': 12
    })

    assert request is not None
    assert request.pkgbase == 'systemd'
    assert request.pkgver == '100'
    assert str(request.message).startswith('New version 101 is available')
    request.save()

    new_request = command.process_package({
        'pkgbase': 'systemd',
        'local_version': 100,
        'upstream_version': 101,
        'out_of_date': True,
        'issue': 12
    })
    assert new_request is None

    request.delete()

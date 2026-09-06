from datetime import datetime, timezone
from unittest import mock

import pytest
from django.core.management import call_command

import packages.management.commands.populate_signoffs  # noqa
from main.models import Arch, Repo
from packages.models import Package, SignoffSpecification


@pytest.fixture
def package(transactional_db, arches, repos):
    repo = Repo.objects.get(name='Extra-Testing')
    arch = Arch.objects.get(name__iexact='any')
    now = datetime.now(tz=timezone.utc)
    package = Package.objects.create(arch=arch, repo=repo, pkgname='systemd',
                                     pkgbase='systemd', pkgver='0.1',
                                     pkgrel='1', pkgdesc='Linux kernel',
                                     compressed_size=10, installed_size=20,
                                     last_update=now, created=now)
    yield package
    package.delete()


def test_basic(package):
    with mock.patch('packages.management.commands.populate_signoffs.get_tag_info') as get_tag_info:
        comment = 'upgpkg: 0.1-1: rebuild'
        get_tag_info.return_value = {'message': f'{comment}\n', 'author': 'foo@archlinux.org'}
        call_command('populate_signoffs')

        signoff_spec = SignoffSpecification.objects.first()
        assert signoff_spec.comments == comment
        assert signoff_spec.pkgbase == package.pkgbase


def test_invalid(package):
    with mock.patch('packages.management.commands.populate_signoffs.get_tag_info') as get_tag_info:
        get_tag_info.return_value = None
        call_command('populate_signoffs')

        assert SignoffSpecification.objects.count() == 0

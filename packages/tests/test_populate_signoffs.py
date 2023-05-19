from unittest import mock
from datetime import datetime, timezone

from django.core.management import call_command
from django.test import TransactionTestCase

from main.models import Arch, Repo
from packages.models import Package, SignoffSpecification
import packages.management.commands.populate_signoffs  # noqa


class RematchDeveloperTest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def setUp(self):
        repo = Repo.objects.get(name='Testing')
        arch = Arch.objects.get(name__iexact='any')
        now = datetime.now(tz=timezone.utc)
        self.package = Package.objects.create(arch=arch, repo=repo, pkgname='systemd',
                                              pkgbase='systemd', pkgver='0.1',
                                              pkgrel='1', pkgdesc='Linux kernel',
                                              compressed_size=10, installed_size=20,
                                              last_update=now, created=now)

    def tearDown(self):
        self.package.delete()

    def test_basic(self):
        with mock.patch('packages.management.commands.populate_signoffs.get_last_log') as get_last_log:
            comment = 'upgpkg: 0.1-1: rebuild'
            get_last_log.return_value = {'message': f'{comment}\n', 'author': 'foo@archlinux.org'}
            call_command('populate_signoffs')

            signoff_spec = SignoffSpecification.objects.first()
            assert signoff_spec.comments == comment
            assert signoff_spec.pkgbase == self.package.pkgbase

    def test_invalid(self):
        with mock.patch('packages.management.commands.populate_signoffs.get_last_log') as get_last_log:
            get_last_log.return_value = None
            call_command('populate_signoffs')

            assert SignoffSpecification.objects.count() == 0

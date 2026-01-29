
from django.test import TransactionTestCase
from django.utils.timezone import now

from devel.management.commands.read_bumpbuddy_status import Command as BumpBuddyCommand
from main.models import Arch, Package, Repo
from packages.models import FlagRequest


class RetireUsertest(TransactionTestCase):
    fixtures = ['main/fixtures/arches.json', 'main/fixtures/repos.json']

    def setUp(self):
        pass

    def process_package(self, pkgdata):
        cmd = BumpBuddyCommand()
        cmd.process_package(pkgdata)

    def test_ood_package(self):
        arch = Arch.objects.get(name='x86_64')
        extra = Repo.objects.get(name='Extra')
        created = now()
        pkg = Package.objects.create(arch=arch, repo=extra, pkgname='systemd',
                                      pkgbase='systemd', pkgver=100,
                                      pkgrel=1, pkgdesc='Linux kernel',
                                      compressed_size=10, installed_size=20,
                                      last_update=created, created=created)

        self.process_package({
            'pkgbase': 'systemd',
            'local_version': 100,
            'upstream_version': 100,
            'out_of_date': False,
            'issue': 12
        })

        flag_requests = FlagRequest.objects.all()
        assert len(flag_requests) == 0

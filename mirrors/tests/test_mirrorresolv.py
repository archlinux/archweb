from unittest import mock

from django.test import TestCase
from django.core.management import call_command

from mirrors.tests import create_mirror_url


class MirrorCheckTest(TestCase):
    def setUp(self):
        self.mirror_url = create_mirror_url()

    def tearDown(self):
        self.mirror_url.delete()

    @mock.patch('socket.getaddrinfo')
    def test_ip4_ip6(self, getaddrinfo):
        getaddrinfo.return_value = [(2, 1, 6, '', ('1.1.1.1', 0)), (10, 1, 6, '', ('1a01:3f8:132:1d96::1', 0, 0, 0))]
        call_command('mirrorresolv')
        self.mirror_url.refresh_from_db()
        self.assertEqual(self.mirror_url.has_ipv4, True)
        self.assertEqual(self.mirror_url.has_ipv6, True)

    @mock.patch('socket.getaddrinfo')
    def test_ip4_only(self, getaddrinfo):
        getaddrinfo.return_value = [(2, 1, 6, '', ('1.1.1.1', 0))]
        call_command('mirrorresolv')
        self.mirror_url.refresh_from_db()
        self.assertEqual(self.mirror_url.has_ipv4, True)
        self.assertEqual(self.mirror_url.has_ipv6, False)

    @mock.patch('socket.getaddrinfo')
    def test_running_twice(self, getaddrinfo):
        getaddrinfo.return_value = [(2, 1, 6, '', ('1.1.1.1', 0)), (10, 1, 6, '', ('1a01:3f8:132:1d96::1', 0, 0, 0))]

        # Check if values changed
        with mock.patch('mirrors.management.commands.mirrorresolv.logger') as logger:
            call_command('mirrorresolv', '-v3')
        self.assertEqual(logger.debug.call_count, 4)

        # running again does not change any values.
        with mock.patch('mirrors.management.commands.mirrorresolv.logger') as logger:
            call_command('mirrorresolv', '-v3')
        self.assertEqual(logger.debug.call_count, 3)

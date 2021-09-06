from django.test import TransactionTestCase

from mirrors.models import MirrorRsync, Mirror


TEST_IPV6 = "2a0b:4342:1a31:410::"
TEST_IPV6_MASK = "2a0b:4342:1a31:410::/64"
TEST_IPV4 = "8.8.8.8"
TEST_IPV4_MASK = "192.168.1.0/24"


class MirrorRsyncTest(TransactionTestCase):
    def setUp(self):
        self.mirror = Mirror.objects.create(name='rmirror',
                                            admin_email='foo@bar.com')

    def tearDown(self):
        self.mirror.delete()

    def test_ipv6(self):
        mirrorrsync = MirrorRsync.objects.create(ip=TEST_IPV6, mirror=self.mirror)
        self.assertEqual(str(mirrorrsync), TEST_IPV6)
        mirrorrsync.delete()

    def test_ipv6_mask(self):
        mirrorsync = MirrorRsync.objects.create(ip=TEST_IPV6_MASK, mirror=self.mirror)
        self.assertEqual(str(mirrorsync), TEST_IPV6_MASK)
        mirrorsync.delete()

    def test_ipv4(self):
        mirrorrsync = MirrorRsync.objects.create(ip=TEST_IPV4, mirror=self.mirror)
        self.assertEqual(str(mirrorrsync), TEST_IPV4)
        mirrorrsync.delete()

    def test_ipv4_mask(self):
        mirrorrsync = MirrorRsync.objects.create(ip=TEST_IPV4_MASK, mirror=self.mirror)
        self.assertEqual(str(mirrorrsync), TEST_IPV4_MASK)
        mirrorrsync.delete()

    def test_invalid(self):
        with self.assertRaises(ValueError) as e:
            MirrorRsync.objects.create(ip="8.8.8.8.8", mirror=self.mirror)
        self.assertIn('does not appear to be an IPv4 or IPv6 address', str(e.exception))

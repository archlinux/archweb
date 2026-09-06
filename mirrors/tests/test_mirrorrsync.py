import pytest

from mirrors.models import Mirror, MirrorRsync

TEST_IPV6 = "2a0b:4342:1a31:410::"
TEST_IPV4 = "8.8.8.8"


@pytest.fixture
def mirror(transactional_db):
    mirror = Mirror.objects.create(name='rmirror', admin_email='foo@bar.com')
    yield mirror
    mirror.delete()


def test_ipv6(mirror):
    mirrorrsync = MirrorRsync.objects.create(ip=TEST_IPV6, mirror=mirror)
    assert str(mirrorrsync) == TEST_IPV6
    mirrorrsync.delete()


def test_ipv4(mirror):
    mirrorrsync = MirrorRsync.objects.create(ip=TEST_IPV4, mirror=mirror)
    assert str(mirrorrsync) == TEST_IPV4
    mirrorrsync.delete()


def test_invalid(mirror):
    with pytest.raises(ValueError) as e:
        MirrorRsync.objects.create(ip="8.8.8.8.8", mirror=mirror)
    assert 'IPv4 Address with more than 4 bytes' in str(e)

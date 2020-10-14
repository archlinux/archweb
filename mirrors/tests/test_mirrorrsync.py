import pytest

from mirrors.models import MirrorRsync


def test_invalid(transactional_db, mirror):
    with pytest.raises(ValueError) as excinfo:
        MirrorRsync.objects.create(ip="8.8.8.8.8", mirror=mirror)
    assert 'IPv4 Address with more than 4 bytes' in str(excinfo)


def test_ipv6(transactional_db, mirror):
    ipv6 = "2a0b:4342:1a31:410::"
    mirrorrsync = MirrorRsync.objects.create(ip=ipv6, mirror=mirror)
    assert str(mirrorrsync) == ipv6
    mirrorrsync.delete()


def test_ipv4(transactional_db, mirror):
    ipv4 = "8.8.8.8"
    mirrorrsync = MirrorRsync.objects.create(ip=ipv4, mirror=mirror)
    assert str(mirrorrsync) == ipv4
    mirrorrsync.delete()

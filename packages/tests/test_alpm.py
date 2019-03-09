import unittest

from packages.alpm import AlpmAPI


alpm = AlpmAPI()


@unittest.skipUnless(alpm.available, "ALPM is unavailable")
def test_version():
    version = alpm.version()
    assert version is not None
    version = version.split(b'.')
    # version is a 3-tuple, e.g., '7.0.2'
    assert 3 == len(version)


@unittest.skipUnless(alpm.available, "ALPM is unavailable")
def test_vercmp():
    assert 0 == alpm.vercmp("1.0", "1.0")
    assert 1 == alpm.vercmp("1.1", "1.0")


@unittest.skipUnless(alpm.available, "ALPM is unavailable")
def test_compare_versions():
    assert alpm.compare_versions("1.0", "<=", "2.0") == True
    assert alpm.compare_versions("1.0", "<", "2.0") == True
    assert alpm.compare_versions("1.0", ">=", "2.0") == False
    assert alpm.compare_versions("1.0", ">", "2.0") == False
    assert alpm.compare_versions("1:1.0", ">", "2.0") == True
    assert alpm.compare_versions("1.0.2", ">=", "2.1.0") == False
    assert alpm.compare_versions("1.0", "=", "1.0") == True
    assert alpm.compare_versions("1.0", "=", "1.0-1") == True
    assert alpm.compare_versions("1.0", "!=", "1.0") == False


def test_behavior_when_unavailable():
    mock_alpm = AlpmAPI()
    mock_alpm.available = False

    assert mock_alpm.version() is None
    assert mock_alpm.vercmp("1.0", "1.0") is None
    assert mock_alpm.compare_versions("1.0", "=", "1.0") is None

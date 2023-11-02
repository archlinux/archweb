import pytest

from packages.alpm import AlpmAPI

alpm = AlpmAPI()


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_version():
    version = alpm.version()
    assert version
    version = version.split(b'.')
    # version is a 3-tuple, e.g., '7.0.2'
    assert len(version) == 3


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_vercmp():
    assert alpm.vercmp("1.0", "1.0") == 0
    assert alpm.vercmp("1.1", "1.0") == 1


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_compare_versions():
    assert alpm.compare_versions("1.0", "<=", "2.0")
    assert alpm.compare_versions("1.0", "<", "2.0")
    assert not alpm.compare_versions("1.0", ">=", "2.0")
    assert not alpm.compare_versions("1.0", ">", "2.0")
    assert alpm.compare_versions("1:1.0", ">", "2.0")
    assert not alpm.compare_versions("1.0.2", ">=", "2.1.0")

    assert alpm.compare_versions("1.0", "=", "1.0")
    assert alpm.compare_versions("1.0", "=", "1.0-1")
    assert not alpm.compare_versions("1.0", "!=", "1.0")


def test_behavior_when_unavailable():
    mock_alpm = AlpmAPI()
    mock_alpm.available = False

    assert mock_alpm.version() is None
    assert mock_alpm.vercmp("1.0", "1.0") is None
    assert mock_alpm.compare_versions("1.0", "=", "1.0") is None

from mirrors.tests.conftest import NAME, HOSTNAME, PROTOCOL


def test_mirror_get_full_url(mirror):
    assert mirror.get_absolute_url() in mirror.get_full_url()
    assert 'http' in mirror.get_full_url('http')

def test_mirror_downstream(mirror):
    assert list(mirror.downstream()) == []

def test_mirror_get_absolute_url(mirror):
    absolute_url = mirror.get_absolute_url()
    expected = '/mirrors/{}/'.format(mirror.name)
    assert absolute_url == expected

def test_mirror_rer(mirror):
    assert NAME in repr(mirror)


def test_checklocation_family(checklocation):
    assert isinstance(checklocation.family, int)

def test_checklocation_ip_version(checklocation):
    assert isinstance(checklocation.ip_version, int)

def test_checklocation_repr(checklocation):
    assert HOSTNAME in repr(checklocation)


def test_mirrorprotocol_repr(mirrorprotocol):
    assert PROTOCOL in repr(mirrorprotocol)

from mirrors.tests.conftest import NAME, HOSTNAME, PROTOCOL, URL


def test_mirrorurl_address_families(mirrorurl):
    assert not mirrorurl.address_families() is None

def test_mirrorurl_hostname(mirrorurl):
    assert mirrorurl.hostname == HOSTNAME

def test_mirrorurl_get_absolute_url(mirrorurl):
    absolute_url = mirrorurl.get_absolute_url()
    expected = '/mirrors/%s/%d/' % (mirrorurl.mirror.name, mirrorurl.pk)
    assert absolute_url == expected

def test_mirrorurl_overview(client, mirrorurl):
    response = client.get('/mirrors/')
    assert response.status_code == 200
    assert mirrorurl.mirror.name in response.content.decode()

def test_mirrorurl_get_full_url(mirrorurl):
    assert 'mirrors/{}'.format(mirrorurl.mirror.name) in mirrorurl.get_full_url()

def test_mirror_url_clean(mirrorurl):
    mirrorurl.clean()
    # TOOD(jelle): this expects HOSTNAME to resolve, maybe mock
    assert mirrorurl.has_ipv4 == True
    assert mirrorurl.has_ipv6 == True

def test_mirrorurl_repr(mirrorurl):
    assert URL in repr(mirrorurl)


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

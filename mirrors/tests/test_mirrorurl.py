from mirrors.tests.conftest import HOSTNAME, URL


def test_mirrorurl_address_families(mirrorurl):
    assert mirrorurl.address_families() is not None


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
    assert f'mirrors/{mirrorurl.mirror.name}' in mirrorurl.get_full_url()


def test_mirror_url_clean(mirrorurl):
    mirrorurl.clean()
    # TODO(jelle): this expects HOSTNAME to resolve, maybe mock
    assert mirrorurl.has_ipv4
    # requires ipv6 on host... mock?
    # assert mirrorurl.has_ipv6 == True


def test_mirrorurl_repr(mirrorurl):
    assert URL in repr(mirrorurl)

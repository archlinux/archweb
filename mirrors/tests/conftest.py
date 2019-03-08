import pytest

from mirrors.models import CheckLocation, MirrorUrl, MirrorProtocol, Mirror


NAME = 'mirror1'
ADMIN_EMAIL = 'admin@archlinux.org'
HOSTNAME = 'archlinux.org'
SOURCE_IP = '127.0.0.1'
COUNTRY = 'DE'
PROTOCOL = 'https'
URL = '{}://{}'.format(PROTOCOL, HOSTNAME)


@pytest.fixture
def mirror(db, name=NAME, admin_email=ADMIN_EMAIL):
        mirror = Mirror.objects.create(name=name,
                                       admin_email=admin_email)
        yield mirror
        mirror.delete()


@pytest.fixture
def checklocation(db, hostname=HOSTNAME, source_ip=SOURCE_IP, country=COUNTRY):
    checkloc = CheckLocation.objects.create(hostname=hostname,
                                            source_ip=source_ip,
                                            country=country)
    yield checkloc
    checkloc.delete()


@pytest.fixture
def mirrorprotocol(db, protocol=PROTOCOL):
        mirror_protocol = MirrorProtocol.objects.create(protocol=protocol)
        yield mirror_protocol
        mirror_protocol.delete()


@pytest.fixture
def mirrorurl(db, mirror, mirrorprotocol, country=COUNTRY,
              url=URL):
        mirror_url = MirrorUrl.objects.create(url=url,
                                              protocol=mirrorprotocol,
                                              mirror=mirror,
                                              country=country)
        yield mirror_url
        mirror_url.delete()

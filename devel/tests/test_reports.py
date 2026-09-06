import pytest
from django.contrib.auth.models import User

from devel.reports import Linkify
from packages.models import PackageRelation


@pytest.fixture
def devel_client(client, arches, repos, package):
    password = 'test'
    user = User.objects.create_superuser('admin',
                                         'admin@archlinux.org',
                                         password)
    client.post('/login/', {
        'username': user.username,
        'password': password
    })

    yield client

    user.delete()


def test_overview(devel_client):
    response = devel_client.get('/devel/')
    assert response.status_code == 200


def test_reports_old(devel_client):
    response = devel_client.get('/devel/reports/old', follow=True)
    assert response.status_code == 200


def test_reports_outofdate(devel_client):
    response = devel_client.get('/devel/reports/long-out-of-date', follow=True)
    assert response.status_code == 200


def test_reports_big(devel_client):
    response = devel_client.get('/devel/reports/big', follow=True)
    assert response.status_code == 200


def test_reports_badcompression(devel_client):
    response = devel_client.get('/devel/reports/badcompression', follow=True)
    assert response.status_code == 200


def test_reports_uncompressed_man(devel_client):
    response = devel_client.get('/devel/reports/uncompressed-man', follow=True)
    assert response.status_code == 200


def test_reports_uncompressed_info(devel_client):
    response = devel_client.get('/devel/reports/uncompressed-info', follow=True)
    assert response.status_code == 200


def test_reports_unneeded_orphans(devel_client):
    response = devel_client.get('/devel/reports/unneeded-orphans', follow=True)
    assert response.status_code == 200


def test_reports_mismatched_signature(devel_client):
    response = devel_client.get('/devel/reports/mismatched-signature', follow=True)
    assert response.status_code == 200


def test_reports_signature_time(devel_client):
    response = devel_client.get('/devel/reports/signature-time', follow=True)
    assert response.status_code == 200


def test_reports_pkgbases(devel_client):
    response = devel_client.get('/devel/reports/old/pkgbases/')
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain'


def test_reports_pkgbases_with_username(devel_client):
    response = devel_client.get('/devel/reports/uncompressed-man/admin/pkgbases/')
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/plain'


def test_reports_pkgbases_invalid_report(devel_client):
    response = devel_client.get('/devel/reports/nonexistent/pkgbases/')
    assert response.status_code == 404


def test_report_filtered_by_maintainer(devel_client):
    user = User.objects.get(username='admin')
    PackageRelation.objects.create(
        pkgbase='linux',
        user=user,
        type=PackageRelation.MAINTAINER,
    )

    response = devel_client.get(
        f'/devel/reports/old/{user.username}/', follow=True)
    assert response.status_code == 200

    pkgbases = {pkg.pkgbase for pkg in response.context['packages']}
    assert pkgbases == {'linux'}


def test_report_pkgbases_filtered_by_maintainer(devel_client):
    user = User.objects.get(username='admin')
    PackageRelation.objects.create(
        pkgbase='linux',
        user=user,
        type=PackageRelation.MAINTAINER,
    )

    response = devel_client.get(
        f'/devel/reports/old/{user.username}/pkgbases/')
    assert response.status_code == 200
    assert response.content.decode().strip() == 'linux'


def test_linkify_escapes_html():
    link = Linkify(href='"><script>alert(1)</script>', title='<img onerror=alert(1)>', desc='<b>xss</b>')
    result = str(link)
    assert '<script>' not in result
    assert '<img' not in result
    assert '<b>' not in result
    assert '&lt;script&gt;' in result

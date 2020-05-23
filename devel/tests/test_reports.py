import pytest


@pytest.fixture
def report_client(user_client, arches, repos, package):
    return user_client


def test_overview(report_client):
    response = report_client.get('/devel/')
    assert response.status_code == 200


def test_reports_old(report_client):
    response = report_client.get('/devel/reports/old', follow=True)
    assert response.status_code == 200


def test_reports_outofdate(report_client):
    response = report_client.get('/devel/reports/long-out-of-date', follow=True)
    assert response.status_code == 200


def test_reports_big(report_client):
    response = report_client.get('/devel/reports/big', follow=True)
    assert response.status_code == 200


def test_reports_badcompression(report_client):
    response = report_client.get('/devel/reports/badcompression', follow=True)
    assert response.status_code == 200


def test_reports_uncompressed_man(report_client):
    response = report_client.get('/devel/reports/uncompressed-man', follow=True)
    assert response.status_code == 200


def test_reports_uncompressed_info(report_client):
    response = report_client.get('/devel/reports/uncompressed-info', follow=True)
    assert response.status_code == 200


def test_reports_unneeded_orphans(report_client):
    response = report_client.get('/devel/reports/unneeded-orphans', follow=True)
    assert response.status_code == 200


def test_reports_mismatched_signature(report_client):
    response = report_client.get('/devel/reports/mismatched-signature', follow=True)
    assert response.status_code == 200


def test_reports_signature_time(report_client):
    response = report_client.get('/devel/reports/signature-time', follow=True)
    assert response.status_code == 200


def test_non_existing_dependencies(report_client):
    response = report_client.get('/devel/reports/non-existing-dependencies', follow=True)
    assert response.status_code == 200

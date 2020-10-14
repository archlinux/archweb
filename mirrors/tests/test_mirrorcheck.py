import time

from http.client import BadStatusLine
from unittest import mock
from urllib.error import HTTPError, URLError
from ssl import CertificateError
from socket import timeout, error

import pytest

from django.utils.timezone import now
from datetime import timedelta

from django.core.management import call_command

from mirrors.models import CheckLocation, MirrorLog
from mirrors.tests.conftest import HOSTNAME, PROTOCOL


def mocked_request(urlopen, Request, return_value):
    urlopen.return_value.read.return_value = return_value
    Request.get_host.return_value = HOSTNAME
    Request.type.return_value = PROTOCOL


def mocked_request_exception(urlopen, Request, excp):
    urlopen.return_value.read.side_effect = excp
    Request.get_host.return_value = HOSTNAME
    Request.type.return_value = PROTOCOL


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_invalid(urlopen, Request, mirrorurl):
    mocked_request(urlopen, Request, 'data')
    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert mirrorlog.error != ''
    assert mirrorlog.is_success == False

@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_valid(urlopen, Request, mirrorurl):
    mocked_request(urlopen, Request, str(int(time.time())))
    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert mirrorlog.error == ''
    assert mirrorlog.is_success == True


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_valid_olddate(urlopen, Request, mirrorurl):
    mocked_request(urlopen, Request, str(int(time.time())))
    date = now() - timedelta(days=600)
    MirrorLog.objects.create(url=mirrorurl, check_time=date)
    call_command('mirrorcheck')
    assert len(MirrorLog.objects.all()) == 1


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_not_found(urlopen, Request, mirrorurl):
    excp = HTTPError('https://archlinux.org/404.txt', 404, 'Not Found', '', None)
    mocked_request_exception(urlopen, Request, excp)
    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert mirrorlog.error == str(excp)
    assert mirrorlog.is_success == False


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_not_found_variant(urlopen, Request, mirrorurl):
    excp = BadStatusLine('')
    mocked_request_exception(urlopen, Request, excp)
    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert 'Exception in processing' in mirrorlog.error
    assert mirrorlog.is_success == False


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_cert_error(urlopen, Request, mirrorurl):
    excp = CertificateError('certificate error')
    mocked_request_exception(urlopen, Request, excp)
    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert 'certificate error' in mirrorlog.error
    assert mirrorlog.is_success == False


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_general_httpexception(urlopen, Request, mirrorurl):
    excp = URLError('550 No such file', '550.txt')
    mocked_request_exception(urlopen, Request, excp)
    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert excp.reason in mirrorlog.error
    assert mirrorlog.is_success == False


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_socket_timeout(urlopen, Request, mirrorurl):
    excp = timeout('timeout')
    mocked_request_exception(urlopen, Request, excp)

    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert 'Connection timed out.' in mirrorlog.error
    assert mirrorlog.is_success == False


@mock.patch('urllib.request.Request')
@mock.patch('urllib.request.urlopen')
def test_socket_error(urlopen, Request, mirrorurl):
    excp = error('error')
    mocked_request_exception(urlopen, Request, excp)

    call_command('mirrorcheck')
    mirrorlog = MirrorLog.objects.first()
    assert str(excp) in mirrorlog.error
    assert mirrorlog.is_success == False


def test_checklocation_fail(db):
    with pytest.raises(CheckLocation.DoesNotExist) as e:
        call_command('mirrorcheck', '-l', '1')
    assert 'CheckLocation matching query does not exist.' == str(e.value)

def test_checklocation_model(checklocation):
    with mock.patch('mirrors.management.commands.mirrorcheck.logger') as logger:
        call_command('mirrorcheck', '-l', '1')
    logger.info.assert_called()

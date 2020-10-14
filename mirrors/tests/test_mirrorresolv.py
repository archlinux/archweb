from unittest import mock

from django.core.management import call_command


@mock.patch('socket.getaddrinfo')
def test_ip4_ip6(getaddrinfo, db, mirrorurl):
    getaddrinfo.return_value = [(2, 1, 6, '', ('1.1.1.1', 0)), (10, 1, 6, '', ('1a01:3f8:132:1d96::1', 0, 0, 0))]
    call_command('mirrorresolv')
    mirrorurl.refresh_from_db()

    assert mirrorurl.has_ipv4 == True
    assert mirrorurl.has_ipv6 == True


@mock.patch('socket.getaddrinfo')
def test_ip4_only(getaddrinfo, db, mirrorurl):
    getaddrinfo.return_value = [(2, 1, 6, '', ('1.1.1.1', 0))]
    call_command('mirrorresolv')
    mirrorurl.refresh_from_db()

    assert mirrorurl.has_ipv4 == True
    assert mirrorurl.has_ipv6 == False

@mock.patch('socket.getaddrinfo')
def test_running_twice(getaddrinfo, db, mirrorurl):
    getaddrinfo.return_value = [(2, 1, 6, '', ('1.1.1.1', 0)), (10, 1, 6, '', ('1a01:3f8:132:1d96::1', 0, 0, 0))]

    # Check if values changed
    with mock.patch('mirrors.management.commands.mirrorresolv.logger') as logger:
        call_command('mirrorresolv', '-v3')
    assert logger.debug.call_count == 4

    # running again does not change any values.
    with mock.patch('mirrors.management.commands.mirrorresolv.logger') as logger:
        call_command('mirrorresolv', '-v3')
    assert logger.debug.call_count == 3

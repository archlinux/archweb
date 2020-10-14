from django.core import mail


def test_flag_package(client, arches, repos, package):
    data = {
        'website': '',
        'email': 'nobody@archlinux.org',
        'message': 'new linux version',
    }
    response = client.post('/packages/core/x86_64/linux/flag/',
                                data,
                                follow=True)
    assert response.status_code == 200
    assert 'Package Flagged - linux' in response.content.decode()
    assert len(mail.outbox) == 1
    assert 'package [linux] marked out-of-date' in mail.outbox[0].subject

    # Flag again, should fail
    response = client.post('/packages/core/x86_64/linux/flag/',
                                data,
                                follow=True)
    assert response.status_code == 200
    assert 'has already been flagged out-of-date.' in response.content.decode()


def test_flag_package_invalid(client, arches, repos, package):
    data = {
        'website': '',
        'email': 'nobody@archlinux.org',
        'message': 'a',
    }
    response = client.post('/packages/core/x86_64/linux/flag/',
                                data,
                                follow=True)
    assert response.status_code == 200
    assert 'Enter a valid and useful out-of-date message' in response.content.decode()
    assert len(mail.outbox) == 0


def test_flag_help(client, arches, repos, package):
    response = client.get('/packages/flaghelp/')
    assert response.status_code == 200

def test_flag_package(client, package, mailoutbox):
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
    assert len(mailoutbox) == 1
    assert 'package [linux] marked out-of-date' in mailoutbox[0].subject

    # Flag again, should fail
    response = client.post('/packages/core/x86_64/linux/flag/',
                           data,
                           follow=True)
    assert response.status_code == 200
    assert 'has already been flagged out-of-date.' in response.content.decode()


def test_flag_package_invalid(client, package, mailoutbox):
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
    assert len(mailoutbox) == 0


def test_flag_package_invalid_denylist(client, package, denylist, mailoutbox):
    data = {
        'website': '',
        'email': 'nobody@archlinux.org',
        'message': 'check out https://bit.ly/4z3rty',
    }
    response = client.post('/packages/core/x86_64/linux/flag/',
                           data,
                           follow=True)
    assert response.status_code == 200
    assert 'Enter a valid and useful out-of-date message' in response.content.decode()
    assert len(mailoutbox) == 0


def test_flag_help(client):
    response = client.get('/packages/flaghelp/')
    assert response.status_code == 200


def assert_flag_developer_package(client):
    data = {
        'website': '',
        'email': 'nobody@archlinux.org',
        'message': 'new linux version',
    }
    response = client.post('/packages/core/x86_64/linux/flag/',
                           data,
                           follow=True)
    assert response.status_code == 200


def test_flag_developer_package(developer_client, package):
    assert_flag_developer_package(developer_client)


def test_unflag_package_404(developer_client, package):
    response = developer_client.get('/packages/core/x86_64/fooobar/unflag/')
    assert response.status_code == 404

    response = developer_client.get('/packages/core/x86_64/fooobar/unflag/all/')
    assert response.status_code == 404


def test_unflag_package(developer_client, package):
    assert_flag_developer_package(developer_client)
    response = developer_client.get('/packages/core/x86_64/linux/unflag/', follow=True)
    assert response.status_code == 200
    assert 'Flag linux as out-of-date' in response.content.decode()


def test_unflag_all_package(developer_client, package):
    assert_flag_developer_package(developer_client)
    response = developer_client.get('/packages/core/x86_64/linux/unflag/all/', follow=True)
    assert response.status_code == 200
    assert 'Flag linux as out-of-date' in response.content.decode()

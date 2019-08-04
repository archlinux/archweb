def assert_flag_package(client):
    data = {
        'website': '',
        'email': 'nobody@archlinux.org',
        'message': 'new linux version',
    }

    # TODO: hardcoded package name
    response = client.post('/packages/core/x86_64/linux/flag/',
                                data,
                                follow=True)
    assert response.status_code == 200


def test_unflag_package_404(admin_user_profile, admin_client):
    response = admin_client.get('/packages/core/x86_64/fooobar/unflag/')
    assert response.status_code == 404

    response = admin_client.get('/packages/core/x86_64/fooobar/unflag/all/')
    assert response.status_code == 404


def test_unflag_package(admin_user_profile, admin_client, package):
    assert_flag_package(admin_client)
    response = admin_client.get('/packages/core/x86_64/linux/unflag/', follow=True)
    assert response.status_code == 200
    assert 'Flag linux as out-of-date' in response.content.decode()


def test_unflag_all_package(admin_user_profile, admin_client, package):
    assert_flag_package(admin_client)
    response = admin_client.get('/packages/core/x86_64/linux/unflag/all/', follow=True)
    assert response.status_code == 200
    assert 'Flag linux as out-of-date' in response.content.decode()

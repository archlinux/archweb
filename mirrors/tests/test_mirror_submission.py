def test_mirror_registration(client, mirrorurl):
    response = client.get('/mirrorlist/submit/?name=test3&tier=2&upstream=1&admin_email=anton%40hvornum.se&alternate_email=&isos=on&rsync_user=&rsync_password=&notes=&active=True&public=True&url1-url=rsync%3A%2F%2Ftest3.com%2Farchlinux&url1-country=SE&url1-bandwidth=1234&url1-active=on&url2-url=&url2-country=&url2-bandwidth=&url2-active=on&url3-url=&url3-country=&url3-bandwidth=&url3-active=on&ip=&captcha_0=d5a017cc3851fb59898167f666759c99b42afd52&captcha_1=tdof')
    assert response.status_code == 200

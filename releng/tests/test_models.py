def test_feed(client, release):
    response = client.get('/feeds/releases/')
    assert response.status_code == 200


def test_absolute_url(release):
    assert release.version in release.get_absolute_url()


def test_iso_url(release):
    url = release.iso_url()
    ver = release.version
    expected = 'iso/{}/archlinux-{}-x86_64.iso'.format(ver, ver)
    assert url == expected


def test_info_html(release):
    assert release.info in release.info_html()


def test_dir_path(release):
    dir_path = u'iso/{}/'.format(release.version)
    assert dir_path == release.dir_path()


def test_sitemap(client, release):
    response = client.get('/sitemap-releases.xml')
    assert response.status_code == 200

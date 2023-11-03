def test_feed(client, release):
    response = client.get('/feeds/releases/')
    assert response.status_code == 200


def test_str(release):
    assert str(release) == release.version


def test_absolute_url(release):
    assert release.version, release.get_absolute_url()


def test_iso_url(release):
    url = release.iso_url()
    ver = release.version
    expected = f'iso/{ver}/archlinux-{ver}-x86_64.iso'
    assert url == expected


def test_info_html(release):
    assert release.info in release.info_html()


def test_dir_path(release):
    dir_path = f'iso/{release.version}/'
    assert dir_path == release.dir_path()


def test_sitemap(client, release):
    response = client.get('/sitemap-releases.xml')
    assert response.status_code == 200


def test_garbage_torrent_data(release):
    assert release.torrent() is None

    release.torrent_data = 'garbage'
    assert release.torrent() is None


def test_torrent_data(release, torrent_data):
    release.torrent_data = torrent_data
    data = release.torrent()
    assert 'arch' in data['file_name']


def test_magnet_uri(release, torrent_data):
    release.torrent_data = torrent_data
    assert release.magnet_uri()

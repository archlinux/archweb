from datetime import datetime, timezone

import pytest

from main.models import Arch, Package, Repo
from packages.alpm import AlpmAPI

alpm = AlpmAPI()


@pytest.fixture
def gnome_backgrounds_packages(db, arches, repos):
    extra = Repo.objects.get(name__iexact='extra')
    multilib = Repo.objects.get(name__iexact='multilib')
    arch = Arch.objects.get(name='x86_64')
    created = datetime.now(tz=timezone.utc)

    def create(repo, pkgname, pkgver):
        return Package.objects.create(
            arch=arch,
            repo=repo,
            pkgname=pkgname,
            pkgbase='gnome-backgrounds',
            pkgver=pkgver,
            pkgrel='1',
            pkgdesc='test',
            compressed_size=1,
            installed_size=1,
            last_update=created,
            created=created,
        )

    return {
        'older': create(extra, 'gnome-backgrounds', '48.2.1'),
        'newer': create(multilib, 'gnome-backgrounds', '49.0'),
        'split': create(extra, 'gnome-backgrounds-extra', '48.2.1'),
    }


def _flag_data():
    return {
        'website': '',
        'email': 'nobody@archlinux.org',
        'message': 'new upstream release',
    }


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_flag_older_does_not_flag_newer(client, gnome_backgrounds_packages, mailoutbox):
    older = gnome_backgrounds_packages['older']
    newer = gnome_backgrounds_packages['newer']
    split = gnome_backgrounds_packages['split']

    response = client.post(
        f'/packages/{older.repo.name.lower()}/{older.arch.name}/{older.pkgname}/flag/',
        _flag_data(),
        follow=True,
    )
    assert response.status_code == 200

    older.refresh_from_db()
    newer.refresh_from_db()
    split.refresh_from_db()
    assert older.flag_date is not None
    assert split.flag_date is not None
    assert newer.flag_date is None


@pytest.mark.skipif(not alpm.available, reason="ALPM is unavailable")
def test_flag_newer_flags_older(client, gnome_backgrounds_packages, mailoutbox):
    older = gnome_backgrounds_packages['older']
    newer = gnome_backgrounds_packages['newer']

    response = client.post(
        f'/packages/{newer.repo.name.lower()}/{newer.arch.name}/{newer.pkgname}/flag/',
        _flag_data(),
        follow=True,
    )
    assert response.status_code == 200

    older.refresh_from_db()
    newer.refresh_from_db()
    assert older.flag_date is not None
    assert newer.flag_date is not None


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

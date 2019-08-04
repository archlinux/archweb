from main.models import Package, Repo
from packages.models import PackageRelation


def request(client, pkgid, adopt=True):
    data = {
        'pkgid': pkgid,
    }
    if adopt:
        data['adopt'] = 'adopt'
    else:
        data['disown'] = 'disown'
    return client.post('/packages/update/', data, follow=True)


def test_wrong_request(admin_client, arches, repos, package):
    # TODO(jelle): fix 
    pkg = Package.objects.first()
    response = admin_client.post('/packages/update/', {'pkgid': pkg.id, }, follow=True)
    assert response.status_code == 200
    assert 'Are you trying to adopt or disown' in response.content.decode()


def test_stale_relations(admin_user_profile, admin_client, arches, repos, package):
    response = admin_client.get('/packages/stale_relations/')
    assert response.status_code == 200


def test_no_permissions(admin_client, admin_user_profile, arches, repos, package):
    pkg = Package.objects.first()

    response = request(admin_client, pkg.id)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 0


def test_adopt_package(admin_client, admin_user_profile, arches, repos, package):
    admin_user_profile.allowed_repos.add(Repo.objects.get(name='Core'))
    pkg = Package.objects.first()
    response = request(admin_client, pkg.id)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 1

    response = request(admin_client, pkg.id, False)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 0

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


def test_stale_relations(user_client, arches, repos, package):
    response = user_client.get('/packages/stale_relations/')
    assert response.status_code == 200


def test_no_permissions(user_client, arches, repos, package):
    pkg = Package.objects.first()

    response = request(user_client, pkg.id)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 0


def test_adopt_package(user_client, userprofile, arches, repos, package):
    userprofile.allowed_repos.add(Repo.objects.get(name='Core'))
    pkg = Package.objects.first()
    response = request(user_client, pkg.id)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 1

    response = request(user_client, pkg.id, False)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 0

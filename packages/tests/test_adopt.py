from main.models import Package
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


def test_adopt_package(developer_client, package):
    pkg = Package.objects.first()
    response = request(developer_client, pkg.id)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 1

    response = request(developer_client, pkg.id, adopt=False)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 0


def test_no_permissions(client, package):
    pkg = Package.objects.first()

    response = request(client, pkg.id)
    assert response.status_code == 200
    assert len(PackageRelation.objects.all()) == 0


def test_wrong_request(developer_client, package):
    pkg = Package.objects.first()
    response = developer_client.post('/packages/update/', {'pkgid': pkg.id, }, follow=True)
    assert response.status_code == 200
    assert 'Are you trying to adopt or disown' in response.content.decode()

from django.utils import timezone

from main.models import Package


def flag_package():
    Package.objects.filter(pkgname='linux').update(flag_date=timezone.now())


def test_unflag_package_404(developer_client, package):
    response = developer_client.get('/packages/core/x86_64/fooobar/unflag/')
    assert response.status_code == 404

    response = developer_client.get('/packages/core/x86_64/fooobar/unflag/all/')
    assert response.status_code == 404


def test_unflag_package(developer_client, package):
    flag_package()
    response = developer_client.get('/packages/core/x86_64/linux/unflag/', follow=True)
    assert response.status_code == 200


def test_unflag_all_package(developer_client, package):
    flag_package()
    response = developer_client.get('/packages/core/x86_64/linux/unflag/all/', follow=True)
    assert response.status_code == 200

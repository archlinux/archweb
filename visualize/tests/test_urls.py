from django.test import Client


def test_urls(client: Client, arches: None, repos: None, package: None) -> None:
    for url in ['', 'by_repo/', 'by_arch/']:
        response = client.get(f'/visualize/{url}')
        assert response.status_code == 200

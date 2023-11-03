def test_urls(client, arches, repos, package):
    for url in ['', 'by_repo/', 'by_arch/']:
        response = client.get(f'/visualize/{url}')
        assert response.status_code == 200

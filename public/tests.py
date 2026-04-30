from django.template import Context, Template


def test_news_preview_filter_chain_preserves_multiline_pre():
    html = (
        "<p>Intro</p>"
        "<pre><code>line one\nline two\nline three</code></pre>"
        "<p>Outro</p>"
    )
    template = Template("{{ html|linebreaks|truncatewords_html:100 }}")
    rendered = template.render(Context({"html": html}))

    assert "line one<br>line two<br>line three" in rendered
    assert "line one line two line three" not in rendered


def test_index(client, arches, repos, package, groups, staff_groups):
    response = client.get('/')
    assert response.status_code == 200


def test_about(client, arches, repos, package, groups, staff_groups):
    response = client.get('/about/')
    assert response.status_code == 200


def test_art(client, arches, repos, package, groups, staff_groups):
    response = client.get('/art/')
    assert response.status_code == 200


def test_donate(client, arches, repos, package, groups, staff_groups):
    response = client.get('/donate/')
    assert response.status_code == 200


def test_download(client, arches, repos, package, groups, staff_groups):
    response = client.get('/download/')
    assert response.status_code == 200


def test_master_keys(client, arches, repos, package, groups, staff_groups):
    response = client.get('/master-keys/')
    assert response.status_code == 200


def test_master_keys_json(client, arches, repos, package, groups, staff_groups):
    response = client.get('/master-keys/json/')
    assert response.status_code == 200


def test_feeds(client, arches, repos, package, groups, staff_groups):
    response = client.get('/feeds/')
    assert response.status_code == 200


def test_people(client, arches, repos, package, groups, staff_groups):
    response = client.get('/people/developers/')
    assert response.status_code == 200


def test_sitemap(client, arches, repos, package, groups, staff_groups):
    sitemaps = ['sitemap', 'sitemap-base']
    for sitemap in sitemaps:
        response = client.get(f'/{sitemap}.xml')
        assert response.status_code == 200

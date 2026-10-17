from django.template import engines
from django.utils.safestring import mark_safe

from main.templatetags.htmltruncate import truncatewords_html_preserve_pre


def test_truncatewords_html_preserve_pre_keeps_pre_newlines():
    html = mark_safe(
        '<p>Intro</p><pre><code>line one\nline two\nline three</code></pre>'
    )
    out = truncatewords_html_preserve_pre(html, 50)
    assert 'line one\nline two' in out
    assert 'line one line two line three' not in out

    engine = engines['django']
    t = engine.from_string('{{ x|truncatewords_html_preserve_pre:50 }}')
    rendered = t.render({'x': html})
    assert 'line one\nline two' in rendered


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

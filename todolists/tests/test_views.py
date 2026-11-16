import pytest

from packages.models import PackageRelation
from todolists.models import Todolist, TodolistPackage


@pytest.fixture
def maintainer(user, todolistpackage):
    PackageRelation.objects.create(pkgbase=todolistpackage.pkgbase, user=user,
                                   type=PackageRelation.MAINTAINER)


def assert_create_todo(client):
    response = client.post('/todo/add/', {
        'name': 'Foo rebuild',
        'description': 'The Foo Rebuild, please read the instructions',
        'raw': 'linux',
        'kind': Todolist.KIND_CHOICES[0][0],  # rebuild
        'stages': Todolist.DEFAULT_STAGES[Todolist.REBUILD],
    }, follow=True)
    assert response.status_code == 200


def test_todolist_overview(developer_client, todolist):
    response = developer_client.get('/todo/')
    assert response.status_code == 200
    assert todolist.name in response.content.decode()


def test_todolist_detail(todolist, developer_client):
    response = developer_client.get(todolist.get_absolute_url())
    assert response.status_code == 200
    assert todolist.name in response.content.decode()


def test_todolist_json(todolist, developer_client):
    response = developer_client.get(todolist.get_absolute_url() + 'json')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == todolist.name


def test_create_todolist(developer_client):
    assert_create_todo(developer_client)
    assert Todolist.objects.count() == 1
    Todolist.objects.all().delete()


def test_flag_pkg(developer_client, arches, repos, package):
    assert_create_todo(developer_client)

    todolist = Todolist.objects.first()
    response = developer_client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 302
    package = todolist.packages().first()
    assert package.status_str == 'Incomplete'
    flag_url = f'/todo/{todolist.slug}/flag/{package.id}/'

    response = developer_client.get(flag_url)
    assert response.status_code == 302

    package = todolist.packages().first()
    assert package.status_str == 'Complete'

    # Flag incomplete again
    response = developer_client.get(flag_url)
    assert response.status_code == 302
    package = todolist.packages().first()
    assert package.status_str == 'Incomplete'

    # Test flagging from JS
    response = developer_client.get(flag_url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    data = response.json()
    assert data['status']
    assert data['css_class']

    Todolist.objects.all().delete()


def test_edit(developer_client, arches, repos, package):
    assert_create_todo(developer_client)

    todolist = Todolist.objects.first()
    assert todolist.packages().count() == 1

    response = developer_client.post(f'/todo/{todolist.slug}/edit/', {
        'name': 'Foo rebuild',
        'description': 'The Foo Rebuild, please read the instructions',
        'raw': 'linux\nglibc',
        'kind': Todolist.KIND_CHOICES[0][0],  # rebuild
    })
    assert response.status_code == 302
    todolist = Todolist.objects.first()
    assert todolist.packages().count() == 2

    Todolist.objects.all().delete()


def test_delete(developer_client, todolist):
    response = developer_client.post(f'/todo/{todolist.slug}/delete')
    assert response.status_code == 301


def test_json_endpoint(developer_client, todolist):
    response = developer_client.post(f'/todo/{todolist.slug}/json')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == todolist.name


def test_add_view(developer_client):
    response = developer_client.post('/todo/add/')
    assert response.status_code == 200


def test_edit_view(developer_client, todolist):
    response = developer_client.get(f'/todo/{todolist.slug}/edit/')
    assert response.status_code == 200


def test_detail_missing_packages_warning(developer_client, todolist, todolistpackage):
    todolist.raw = f'{todolistpackage.pkgname}\nnonexistent-pkg'
    todolist.save()
    response = developer_client.get(todolist.get_absolute_url())
    content = response.content.decode()
    assert 'todo-warning' in content
    assert 'nonexistent-pkg' in content


def test_detail_no_missing_packages_warning(developer_client, todolist, todolistpackage):
    todolist.raw = todolistpackage.pkgname
    todolist.save()
    response = developer_client.get(todolist.get_absolute_url())
    assert 'todo-warning' not in response.content.decode()


def test_add_view_default_stages(developer_client):
    response = developer_client.get('/todo/add/')
    form = response.context['form']
    assert form.fields['stages'].initial == Todolist.DEFAULT_STAGES[Todolist.REBUILD]
    # used to select the default stages when changing the kind
    assert response.context['default_stages'] == Todolist.DEFAULT_STAGES
    assert 'id="default-stages"' in response.content.decode()


def test_create_todolist_requires_stages(developer_client):
    response = developer_client.post('/todo/add/', {
        'name': 'Foo',
        'description': 'Foo',
        'raw': 'linux',
        'kind': Todolist.REBUILD,
    })
    assert response.status_code == 200
    assert 'stages' in response.context['form'].errors
    assert not Todolist.objects.exists()


def test_create_todolist_custom_stages(developer_client):
    response = developer_client.post('/todo/add/', {
        'name': 'Foo',
        'description': 'Foo',
        'raw': 'linux',
        'kind': Todolist.REBUILD,
        'stages': ['rebuild_testing', 'draft'],
    })
    assert response.status_code == 302
    assert Todolist.objects.get().stages == ['draft', 'rebuild_testing']
    Todolist.objects.all().delete()


def test_edit_keeps_stages(developer_client, todolist):
    response = developer_client.get(f'/todo/{todolist.slug}/edit/')
    assert 'stages' not in response.context['form'].fields

    response = developer_client.post(f'/todo/{todolist.slug}/edit/', {
        'name': todolist.name,
        'description': todolist.description,
        'raw': todolist.raw,
        'kind': Todolist.REBUILD,
        'stages': ['in_progress'],
    })
    assert response.status_code == 302
    todolist.refresh_from_db()
    assert todolist.stages == Todolist.DEFAULT_STAGES[Todolist.REBUILD]


def test_create_todolist_no_email_in_draft(developer_client, arches, repos, package, user, mailoutbox):
    PackageRelation.objects.create(pkgbase='linux', user=user, type=PackageRelation.MAINTAINER)
    assert_create_todo(developer_client)
    assert len(mailoutbox) == 0
    Todolist.objects.all().delete()


def test_create_todolist_email_in_per_package_stage(developer_client, arches, repos, package, user,
                                                    mailoutbox):
    PackageRelation.objects.create(pkgbase='linux', user=user, type=PackageRelation.MAINTAINER)
    response = developer_client.post('/todo/add/', {
        'name': 'Foo',
        'description': 'Foo',
        'raw': 'linux',
        'kind': Todolist.TASK,
        'stages': ['in_progress'],
    })
    assert response.status_code == 302
    assert len(mailoutbox) == 1
    assert 'Packages added to todo list' in mailoutbox[0].subject
    Todolist.objects.all().delete()


def test_advance(developer_client, todolist, todolistpackage, maintainer, mailoutbox):
    response = developer_client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 302
    todolist.refresh_from_db()
    todolistpackage.refresh_from_db()
    assert todolist.progress == 1
    assert todolistpackage.progress == 1
    assert len(mailoutbox) == 1
    assert 'reached stage \'Rebuild in staging\'' in mailoutbox[0].subject
    assert todolistpackage.pkgname in mailoutbox[0].body


def test_advance_no_email_for_complete_packages(developer_client, todolist, todolistpackage, maintainer,
                                                mailoutbox):
    todolistpackage.progress = 2
    todolistpackage.save()
    response = developer_client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 302
    todolistpackage.refresh_from_db()
    assert todolistpackage.progress == 2
    assert len(mailoutbox) == 0


def test_advance_no_email_for_non_per_package_stage(developer_client, todolist, todolistpackage, maintainer,
                                                    mailoutbox):
    todolist.progress = 1
    todolist.save()
    todolistpackage.progress = 2
    todolistpackage.save()
    response = developer_client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 302
    todolist.refresh_from_db()
    assert todolist.current_stage.key == 'test_testing'
    assert len(mailoutbox) == 0


def test_advance_incomplete_packages(developer_client, todolist, todolistpackage):
    todolist.progress = 1
    todolist.save()
    todolistpackage.progress = 1
    todolistpackage.save()
    response = developer_client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 400
    todolist.refresh_from_db()
    assert todolist.progress == 1


def test_advance_finished(developer_client, todolist):
    todolist.progress = 3
    todolist.save()
    response = developer_client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 400


def test_advance_get(developer_client, todolist):
    response = developer_client.get(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 405


def test_advance_permission(client, todolist):
    response = client.post(f'/todo/{todolist.slug}/advance/')
    assert response.status_code == 302
    todolist.refresh_from_db()
    assert todolist.progress == 0


def test_back(developer_client, todolist, todolistpackage, mailoutbox):
    todolist.progress = 2
    todolist.save()
    todolistpackage.progress = 2
    todolistpackage.save()
    response = developer_client.post(f'/todo/{todolist.slug}/back/')
    assert response.status_code == 302
    todolist.refresh_from_db()
    todolistpackage.refresh_from_db()
    assert todolist.progress == 1
    # packages keep their completion status
    assert todolistpackage.progress == 2
    assert todolistpackage.is_complete
    assert len(mailoutbox) == 0


def test_back_first_stage(developer_client, todolist):
    response = developer_client.post(f'/todo/{todolist.slug}/back/')
    assert response.status_code == 400


def test_flag_non_per_package_stage(developer_client, todolist, todolistpackage):
    response = developer_client.get(f'/todo/{todolist.slug}/flag/{todolistpackage.id}/')
    assert response.status_code == 400


def test_flag_last_package_emails_owner(developer_client, todolist, todolistpackage, mailoutbox):
    todolist.progress = 1
    todolist.save()
    todolistpackage.progress = 1
    todolistpackage.save()
    response = developer_client.get(f'/todo/{todolist.slug}/flag/{todolistpackage.id}/')
    assert response.status_code == 302
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [todolist.creator.email]
    assert 'completed stage \'Rebuild in staging\'' in mailoutbox[0].subject


def test_flag_remaining_packages_no_email(developer_client, todolist, todolistpackage, mailoutbox):
    todolist.progress = 1
    todolist.save()
    todolistpackage.progress = 1
    todolistpackage.save()
    other = TodolistPackage.objects.create(pkg=todolistpackage.pkg, pkgname='other',
                                           pkgbase='other', arch=todolistpackage.arch,
                                           repo=todolistpackage.repo, todolist=todolist,
                                           progress=1)
    response = developer_client.get(f'/todo/{todolist.slug}/flag/{todolistpackage.id}/')
    assert response.status_code == 302
    assert len(mailoutbox) == 0
    other.delete()


def test_detail_stages(developer_client, todolist, todolistpackage):
    response = developer_client.get(todolist.get_absolute_url())
    content = response.content.decode()
    assert 'Current stage: Draft' in content
    assert 'Start task' in content
    assert 'Back to previous stage' not in content


def test_detail_finished(developer_client, todolist):
    todolist.progress = 3
    todolist.save()
    response = developer_client.get(todolist.get_absolute_url())
    content = response.content.decode()
    assert 'This todo list is complete.' in content
    assert 'Back to previous stage' in content


def test_todolist_overview_stage(developer_client, todolist):
    response = developer_client.get('/todo/')
    assert 'Draft' in response.content.decode()


def test_detail_status_per_package_stage_only(developer_client, todolist, todolistpackage):
    response = developer_client.get(todolist.get_absolute_url())
    content = response.content.decode()
    assert '<th>Status</th>' not in content
    assert 'id_incomplete' not in content

    todolist.progress = 1
    todolist.save()
    response = developer_client.get(todolist.get_absolute_url())
    content = response.content.decode()
    assert '<th>Status</th>' in content
    assert 'id_incomplete' in content


@pytest.mark.parametrize('url', ['/todo/', '/devel/'])
def test_incomplete_count_per_package_stage_only(developer_client, todolist, todolistpackage, url):
    # the only package is complete, so the incomplete count is 0
    todolistpackage.progress = 2
    todolistpackage.save()
    response = developer_client.get(url)
    assert '<td>0</td>' not in response.content.decode()

    todolist.progress = 1
    todolist.save()
    response = developer_client.get(url)
    assert '<td>0</td>' in response.content.decode()


def test_dashboard_incomplete_packages(developer_client, todolist, todolistpackage, maintainer):
    # nothing to do for maintainers in stages without per-package completion
    response = developer_client.get('/devel/')
    assert response.context['todopkgs'] == []

    todolist.progress = 1
    todolist.save()
    todolistpackage.progress = 1
    todolistpackage.save()
    response = developer_client.get('/devel/')
    assert response.context['todopkgs'] == [todolistpackage]

    todolistpackage.progress = 2
    todolistpackage.save()
    response = developer_client.get('/devel/')
    assert response.context['todopkgs'] == []


def test_detail_overlapping_rebuild_warning(developer_client, user, todolist, todolistpackage):
    other = Todolist.objects.create(name='Other rebuild', description='Other rebuild',
                                    slug='other-rebuild', creator=user,
                                    stages=Todolist.DEFAULT_STAGES[Todolist.REBUILD])
    TodolistPackage.objects.create(todolist=other, pkg=todolistpackage.pkg,
                                   pkgname=todolistpackage.pkgname,
                                   pkgbase=todolistpackage.pkgbase,
                                   arch=todolistpackage.arch, repo=todolistpackage.repo)
    response = developer_client.get(todolist.get_absolute_url())
    content = response.content.decode()
    assert 'The active rebuild' in content
    assert other.get_absolute_url() in content
    other.delete()


def test_detail_user_without_profile(admin_client, todolist, todolistpackage):
    response = admin_client.get(todolist.get_absolute_url())
    assert response.status_code == 200

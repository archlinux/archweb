import pytest

from django.core.management import call_command



@pytest.fixture
def arches(db):
    call_command('loaddata', 'main/fixtures/arches.json')


@pytest.fixture
def repos(db):
    call_command('loaddata', 'main/fixtures/repos.json')


@pytest.fixture
def package(db):
    # TODO(jelle): create own parameter based version
    call_command('loaddata', 'main/fixtures/package.json')

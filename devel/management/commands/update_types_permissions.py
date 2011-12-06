from django.core.management.base import BaseCommand
from django.db.models import get_models, get_app
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.management import update_contenttypes


class Command(BaseCommand):
    args = '<app app ...>'
    help = 'reloads permissions for specified apps, or all apps if no args are specified'

    def handle(self, *args, **options):
        if not args:
            apps = []
            for model in get_models():
                apps.append(get_app(model._meta.app_label))
        else:
            apps = []
            for arg in args:
                apps.append(get_app(arg))

        for app in apps:
            update_contenttypes(app, None, options.get('verbosity', 2), interactive=True)
            create_permissions(app, get_models(), options.get('verbosity', 0))

# vim: set ts=4 sw=4 et:

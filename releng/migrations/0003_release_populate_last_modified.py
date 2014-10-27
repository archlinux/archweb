# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards(apps, schema_editor):
    Release = apps.get_model('releng', 'Release')
    Release.objects.update(last_modified=models.F('created'))

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('releng', '0002_release_last_modified'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]

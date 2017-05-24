# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releng', '0003_release_populate_last_modified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='modules',
            field=models.ManyToManyField(to='releng.Module', blank=True),
        ),
        migrations.AlterField(
            model_name='test',
            name='rollback_modules',
            field=models.ManyToManyField(related_name='rollback_test_set', to='releng.Module', blank=True),
        ),
        migrations.AlterField(
            model_name='test',
            name='user_email',
            field=models.EmailField(max_length=254, verbose_name=b'email address'),
        ),
    ]

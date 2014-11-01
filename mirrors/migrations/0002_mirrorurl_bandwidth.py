# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mirrors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mirrorurl',
            name='bandwidth',
            field=models.FloatField(null=True, verbose_name=b'bandwidth (mbits)', blank=True),
            preserve_default=True,
        ),
    ]

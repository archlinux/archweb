# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('releng', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2001, 1, 1, tzinfo=utc), editable=False),
            preserve_default=False,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=255)),
                ('postdate', models.DateTimeField(verbose_name=b'post date', db_index=True)),
                ('last_modified', models.DateTimeField(editable=False, db_index=True)),
                ('title', models.CharField(max_length=255)),
                ('guid', models.CharField(max_length=255, editable=False)),
                ('content', models.TextField()),
                ('safe_mode', models.BooleanField(default=True)),
                ('author', models.ForeignKey(related_name=b'news_author', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-postdate',),
                'db_table': 'news',
                'verbose_name_plural': 'news',
                'get_latest_by': 'postdate',
            },
            bases=(models.Model,),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Todolist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=255)),
                ('old_id', models.IntegerField(unique=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('created', models.DateTimeField(db_index=True)),
                ('last_modified', models.DateTimeField(editable=False)),
                ('raw', models.TextField(blank=True)),
                ('creator', models.ForeignKey(related_name=b'created_todolists', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TodolistPackage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pkgname', models.CharField(max_length=255)),
                ('pkgbase', models.CharField(max_length=255)),
                ('created', models.DateTimeField(editable=False)),
                ('last_modified', models.DateTimeField(editable=False)),
                ('removed', models.DateTimeField(null=True, blank=True)),
                ('status', models.SmallIntegerField(default=0, choices=[(0, b'Incomplete'), (1, b'Complete'), (2, b'In-progress')])),
                ('comments', models.TextField(null=True, blank=True)),
                ('arch', models.ForeignKey(to='main.Arch')),
                ('pkg', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='main.Package', null=True)),
                ('repo', models.ForeignKey(to='main.Repo')),
                ('todolist', models.ForeignKey(to='todolists.Todolist')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='todolistpackage',
            unique_together=set([('todolist', 'pkgname', 'arch')]),
        ),
    ]

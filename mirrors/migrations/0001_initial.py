# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_countries.fields
import django.db.models.deletion
import mirrors.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CheckLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hostname', models.CharField(max_length=255)),
                ('source_ip', models.GenericIPAddressField(unique=True, verbose_name=b'source IP', unpack_ipv4=True)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('created', models.DateTimeField(editable=False)),
            ],
            options={
                'ordering': ('hostname', 'source_ip'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Mirror',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('tier', models.SmallIntegerField(default=2, choices=[(0, b'Tier 0'), (1, b'Tier 1'), (2, b'Tier 2'), (-1, b'Untiered')])),
                ('admin_email', models.EmailField(max_length=255, blank=True)),
                ('alternate_email', models.EmailField(max_length=255, blank=True)),
                ('public', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('isos', models.BooleanField(default=True, verbose_name=b'ISOs')),
                ('rsync_user', models.CharField(default=b'', max_length=50, blank=True)),
                ('rsync_password', models.CharField(default=b'', max_length=50, blank=True)),
                ('bug', models.PositiveIntegerField(null=True, verbose_name=b'Flyspray bug', blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created', models.DateTimeField(editable=False)),
                ('last_modified', models.DateTimeField(editable=False)),
                ('upstream', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='mirrors.Mirror', null=True)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MirrorLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('check_time', models.DateTimeField(db_index=True)),
                ('last_sync', models.DateTimeField(null=True)),
                ('duration', models.FloatField(null=True)),
                ('is_success', models.BooleanField(default=True)),
                ('error', models.TextField(default=b'', blank=True)),
                ('location', models.ForeignKey(related_name=b'logs', to='mirrors.CheckLocation', null=True)),
            ],
            options={
                'get_latest_by': 'check_time',
                'verbose_name': 'mirror check log',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MirrorProtocol',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('protocol', models.CharField(unique=True, max_length=10)),
                ('is_download', models.BooleanField(default=True, help_text=b'Is protocol useful for end-users, e.g. HTTP')),
                ('default', models.BooleanField(default=True, help_text=b'Included by default when building mirror list?')),
                ('created', models.DateTimeField(editable=False)),
            ],
            options={
                'ordering': ('protocol',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MirrorRsync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', mirrors.fields.IPNetworkField(max_length=44, verbose_name=b'IP')),
                ('created', models.DateTimeField(editable=False)),
                ('mirror', models.ForeignKey(related_name=b'rsync_ips', to='mirrors.Mirror')),
            ],
            options={
                'ordering': ('ip',),
                'verbose_name': 'mirror rsync IP',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MirrorUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(unique=True, max_length=255, verbose_name=b'URL')),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, db_index=True)),
                ('has_ipv4', models.BooleanField(default=True, verbose_name=b'IPv4 capable', editable=False)),
                ('has_ipv6', models.BooleanField(default=False, verbose_name=b'IPv6 capable', editable=False)),
                ('created', models.DateTimeField(editable=False)),
                ('active', models.BooleanField(default=True)),
                ('mirror', models.ForeignKey(related_name=b'urls', to='mirrors.Mirror')),
                ('protocol', models.ForeignKey(related_name=b'urls', on_delete=django.db.models.deletion.PROTECT, editable=False, to='mirrors.MirrorProtocol')),
            ],
            options={
                'verbose_name': 'mirror URL',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='mirrorlog',
            name='url',
            field=models.ForeignKey(related_name=b'logs', to='mirrors.MirrorUrl'),
            preserve_default=True,
        ),
    ]

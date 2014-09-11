# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Architecture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Bootloader',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BootType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClockChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Filesystem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HardwareType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstallType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Iso',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('created', models.DateTimeField(editable=False)),
                ('removed', models.DateTimeField(default=None, null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'ISO',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IsoType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'ISO type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('release_date', models.DateField(db_index=True)),
                ('version', models.CharField(unique=True, max_length=50)),
                ('kernel_version', models.CharField(max_length=50, blank=True)),
                ('md5_sum', models.CharField(max_length=32, verbose_name=b'MD5 digest', blank=True)),
                ('sha1_sum', models.CharField(max_length=40, verbose_name=b'SHA1 digest', blank=True)),
                ('created', models.DateTimeField(editable=False)),
                ('available', models.BooleanField(default=True)),
                ('info', models.TextField(verbose_name=b'Public information', blank=True)),
                ('torrent_data', models.TextField(help_text=b'base64-encoded torrent file', blank=True)),
            ],
            options={
                'ordering': ('-release_date', '-version'),
                'get_latest_by': 'release_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_name', models.CharField(max_length=500)),
                ('user_email', models.EmailField(max_length=75, verbose_name=b'email address')),
                ('ip_address', models.GenericIPAddressField(verbose_name=b'IP address', unpack_ipv4=True)),
                ('created', models.DateTimeField(editable=False)),
                ('success', models.BooleanField(default=True)),
                ('comments', models.TextField(null=True, blank=True)),
                ('architecture', models.ForeignKey(to='releng.Architecture')),
                ('boot_type', models.ForeignKey(to='releng.BootType')),
                ('bootloader', models.ForeignKey(to='releng.Bootloader')),
                ('clock_choice', models.ForeignKey(to='releng.ClockChoice')),
                ('filesystem', models.ForeignKey(to='releng.Filesystem')),
                ('hardware_type', models.ForeignKey(to='releng.HardwareType')),
                ('install_type', models.ForeignKey(to='releng.InstallType')),
                ('iso', models.ForeignKey(to='releng.Iso')),
                ('iso_type', models.ForeignKey(to='releng.IsoType')),
                ('modules', models.ManyToManyField(to='releng.Module', null=True, blank=True)),
                ('rollback_filesystem', models.ForeignKey(related_name=b'rollback_test_set', blank=True, to='releng.Filesystem', null=True)),
                ('rollback_modules', models.ManyToManyField(related_name=b'rollback_test_set', null=True, to='releng.Module', blank=True)),
                ('source', models.ForeignKey(to='releng.Source')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

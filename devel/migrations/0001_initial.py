# -*- coding: utf-8 -*-

import pytz

from django.db import models, migrations
import django_countries.fields
import django.db.models.deletion
from django.conf import settings
import devel.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeveloperKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', devel.fields.PGPKeyField(unique=True, max_length=40, verbose_name=b'PGP key fingerprint')),
                ('created', models.DateTimeField()),
                ('expires', models.DateTimeField(null=True, blank=True)),
                ('revoked', models.DateTimeField(null=True, blank=True)),
                ('owner', models.ForeignKey(related_name=b'all_keys', to=settings.AUTH_USER_MODEL, help_text=b'The developer this key belongs to', null=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='devel.DeveloperKey', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MasterKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pgp_key', devel.fields.PGPKeyField(help_text=b'consists of 40 hex digits; use `gpg --fingerprint`', max_length=40, verbose_name=b'PGP key fingerprint')),
                ('created', models.DateField()),
                ('revoked', models.DateField(null=True, blank=True)),
                ('owner', models.ForeignKey(related_name=b'masterkey_owner', to=settings.AUTH_USER_MODEL, help_text=b'The developer holding this master key')),
                ('revoker', models.ForeignKey(related_name=b'masterkey_revoker', to=settings.AUTH_USER_MODEL, help_text=b'The developer holding the revocation certificate')),
            ],
            options={
                'ordering': ('created',),
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PGPSignature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('signer', devel.fields.PGPKeyField(max_length=40, verbose_name=b'Signer key fingerprint', db_index=True)),
                ('signee', devel.fields.PGPKeyField(max_length=40, verbose_name=b'Signee key fingerprint', db_index=True)),
                ('created', models.DateField()),
                ('expires', models.DateField(null=True, blank=True)),
                ('revoked', models.DateField(null=True, blank=True)),
            ],
            options={
                'ordering': ('signer', 'signee'),
                'get_latest_by': 'created',
                'verbose_name': 'PGP signature',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notify', models.BooleanField(default=True, help_text=b"When enabled, send user 'flag out-of-date' notifications", verbose_name=b'Send notifications')),
                ('time_zone', models.CharField(default=b'UTC', help_text=b'Used for developer clock page', max_length=100, choices=[(z, z) for z in pytz.common_timezones])),
                ('alias', models.CharField(help_text=b'Required field', max_length=50)),
                ('public_email', models.CharField(help_text=b'Required field', max_length=50)),
                ('other_contact', models.CharField(max_length=100, null=True, blank=True)),
                ('pgp_key', devel.fields.PGPKeyField(help_text=b'consists of 40 hex digits; use `gpg --fingerprint`', max_length=40, null=True, verbose_name=b'PGP key fingerprint', blank=True)),
                ('website', models.CharField(max_length=200, null=True, blank=True)),
                ('yob', models.IntegerField(null=True, verbose_name=b'Year of birth', blank=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2)),
                ('location', models.CharField(max_length=50, null=True, blank=True)),
                ('languages', models.CharField(max_length=50, null=True, blank=True)),
                ('interests', models.CharField(max_length=255, null=True, blank=True)),
                ('occupation', models.CharField(max_length=50, null=True, blank=True)),
                ('roles', models.CharField(max_length=255, null=True, blank=True)),
                ('favorite_distros', models.CharField(max_length=255, null=True, blank=True)),
                ('picture', models.FileField(default=b'devs/silhouette.png', help_text=b'Ideally 125px by 125px', upload_to=b'devs')),
                ('latin_name', models.CharField(help_text=b'Latin-form name; used only for non-Latin full names', max_length=255, null=True, blank=True)),
                ('last_modified', models.DateTimeField(editable=False)),
                ('allowed_repos', models.ManyToManyField(to='main.Repo', blank=True)),
                ('user', models.OneToOneField(related_name=b'userprofile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'last_modified',
                'verbose_name': 'additional profile data',
                'verbose_name_plural': 'additional profile data',
                'db_table': 'user_profiles',
            },
            bases=(models.Model,),
        ),
    ]

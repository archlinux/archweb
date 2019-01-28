# -*- coding: utf-8 -*-


from django.db import models, migrations
import main.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Arch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('agnostic', models.BooleanField(default=False, help_text='Is this architecture non-platform specific?')),
                ('required_signoffs', models.PositiveIntegerField(default=2, help_text='Number of signoffs required for packages of this architecture')),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'arches',
                'verbose_name_plural': 'arches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Donor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('visible', models.BooleanField(default=True, help_text='Should we show this donor on the public page?')),
                ('created', models.DateTimeField()),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'donors',
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pkgname', models.CharField(max_length=255)),
                ('pkgbase', models.CharField(max_length=255, db_index=True)),
                ('pkgver', models.CharField(max_length=255)),
                ('pkgrel', models.CharField(max_length=255)),
                ('epoch', models.PositiveIntegerField(default=0)),
                ('pkgdesc', models.TextField(null=True, verbose_name='description')),
                ('url', models.CharField(max_length=255, null=True, verbose_name='URL')),
                ('filename', models.CharField(max_length=255)),
                ('compressed_size', main.fields.PositiveBigIntegerField()),
                ('installed_size', main.fields.PositiveBigIntegerField()),
                ('build_date', models.DateTimeField(null=True)),
                ('last_update', models.DateTimeField(db_index=True)),
                ('files_last_update', models.DateTimeField(null=True, blank=True)),
                ('created', models.DateTimeField()),
                ('packager_str', models.CharField(max_length=255, verbose_name='packager string')),
                ('signature_bytes', models.BinaryField(verbose_name='PGP signature', null=True)),
                ('flag_date', models.DateTimeField(null=True, blank=True)),
                ('arch', models.ForeignKey(related_name='packages', on_delete=django.db.models.deletion.PROTECT, to='main.Arch')),
                ('packager', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('pkgname',),
                'db_table': 'packages',
                'get_latest_by': 'last_update',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PackageFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_directory', models.BooleanField(default=False)),
                ('directory', models.CharField(max_length=1024)),
                ('filename', models.CharField(max_length=1024, null=True, blank=True)),
                ('pkg', models.ForeignKey(to='main.Package', on_delete=django.db.models.CASCADE)),
            ],
            options={
                'db_table': 'package_files',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('testing', models.BooleanField(default=False, help_text='Is this repo meant for package testing?')),
                ('staging', models.BooleanField(default=False, help_text='Is this repo meant for package staging?')),
                ('bugs_project', models.SmallIntegerField(default=1, help_text='Flyspray project ID for this repository.')),
                ('bugs_category', models.SmallIntegerField(default=2, help_text='Flyspray category ID for this repository.')),
                ('svn_root', models.CharField(help_text='SVN root (e.g. path) for this repository.', max_length=64)),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'repos',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='package',
            name='repo',
            field=models.ForeignKey(related_name='packages', on_delete=django.db.models.deletion.PROTECT, to='main.Repo'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='package',
            unique_together=set([('pkgname', 'repo', 'arch')]),
        ),
    ]

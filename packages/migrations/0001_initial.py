# -*- coding: utf-8 -*-


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
            name='Conflict',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('version', models.CharField(default=b'', max_length=255)),
                ('comparison', models.CharField(default=b'', max_length=255)),
                ('pkg', models.ForeignKey(related_name=b'conflicts', to='main.Package')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Depend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('version', models.CharField(default=b'', max_length=255)),
                ('comparison', models.CharField(default=b'', max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('deptype', models.CharField(default=b'D', max_length=1, choices=[(b'D', b'Depend'), (b'O', b'Optional Depend'), (b'M', b'Make Depend'), (b'C', b'Check Depend')])),
                ('pkg', models.ForeignKey(related_name=b'depends', to='main.Package')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FlagRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_email', models.EmailField(max_length=75, verbose_name=b'email address')),
                ('created', models.DateTimeField(editable=False, db_index=True)),
                ('ip_address', models.GenericIPAddressField(verbose_name=b'IP address', unpack_ipv4=True)),
                ('pkgbase', models.CharField(max_length=255, db_index=True)),
                ('pkgver', models.CharField(max_length=255)),
                ('pkgrel', models.CharField(max_length=255)),
                ('epoch', models.PositiveIntegerField(default=0)),
                ('num_packages', models.PositiveIntegerField(default=1, verbose_name=b'number of packages')),
                ('message', models.TextField(verbose_name=b'message to developer', blank=True)),
                ('is_spam', models.BooleanField(default=False, help_text=b'Is this comment from a real person?')),
                ('is_legitimate', models.BooleanField(default=True, help_text=b'Is this actually an out-of-date flag request?')),
                ('repo', models.ForeignKey(to='main.Repo')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('pkg', models.ForeignKey(related_name=b'licenses', to='main.Package')),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PackageGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('pkg', models.ForeignKey(related_name=b'groups', to='main.Package')),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PackageRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pkgbase', models.CharField(max_length=255)),
                ('type', models.PositiveIntegerField(default=1, choices=[(1, b'Maintainer'), (2, b'Watcher')])),
                ('created', models.DateTimeField(editable=False)),
                ('user', models.ForeignKey(related_name=b'package_relations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Provision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('version', models.CharField(default=b'', max_length=255)),
                ('pkg', models.ForeignKey(related_name=b'provides', to='main.Package')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Replacement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('version', models.CharField(default=b'', max_length=255)),
                ('comparison', models.CharField(default=b'', max_length=255)),
                ('pkg', models.ForeignKey(related_name=b'replaces', to='main.Package')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Signoff',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pkgbase', models.CharField(max_length=255, db_index=True)),
                ('pkgver', models.CharField(max_length=255)),
                ('pkgrel', models.CharField(max_length=255)),
                ('epoch', models.PositiveIntegerField(default=0)),
                ('created', models.DateTimeField(editable=False, db_index=True)),
                ('revoked', models.DateTimeField(null=True)),
                ('comments', models.TextField(null=True, blank=True)),
                ('arch', models.ForeignKey(to='main.Arch')),
                ('repo', models.ForeignKey(to='main.Repo')),
                ('user', models.ForeignKey(related_name=b'package_signoffs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SignoffSpecification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pkgbase', models.CharField(max_length=255, db_index=True)),
                ('pkgver', models.CharField(max_length=255)),
                ('pkgrel', models.CharField(max_length=255)),
                ('epoch', models.PositiveIntegerField(default=0)),
                ('created', models.DateTimeField(editable=False)),
                ('required', models.PositiveIntegerField(default=2, help_text=b'How many signoffs are required for this package?')),
                ('enabled', models.BooleanField(default=True, help_text=b'Is this package eligible for signoffs?')),
                ('known_bad', models.BooleanField(default=False, help_text=b'Is package is known to be broken in some way?')),
                ('comments', models.TextField(null=True, blank=True)),
                ('arch', models.ForeignKey(to='main.Arch')),
                ('repo', models.ForeignKey(to='main.Repo')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pkgname', models.CharField(max_length=255, db_index=True)),
                ('pkgbase', models.CharField(max_length=255)),
                ('action_flag', models.PositiveSmallIntegerField(verbose_name=b'action flag', choices=[(1, b'Addition'), (2, b'Change'), (3, b'Deletion')])),
                ('created', models.DateTimeField(editable=False, db_index=True)),
                ('old_pkgver', models.CharField(max_length=255, null=True)),
                ('old_pkgrel', models.CharField(max_length=255, null=True)),
                ('old_epoch', models.PositiveIntegerField(null=True)),
                ('new_pkgver', models.CharField(max_length=255, null=True)),
                ('new_pkgrel', models.CharField(max_length=255, null=True)),
                ('new_epoch', models.PositiveIntegerField(null=True)),
                ('arch', models.ForeignKey(related_name=b'updates', to='main.Arch')),
                ('package', models.ForeignKey(related_name=b'updates', on_delete=django.db.models.deletion.SET_NULL, to='main.Package', null=True)),
                ('repo', models.ForeignKey(related_name=b'updates', to='main.Repo')),
            ],
            options={
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='packagerelation',
            unique_together=set([('pkgbase', 'user', 'type')]),
        ),
    ]

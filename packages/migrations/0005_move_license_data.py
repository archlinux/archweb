# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    depends_on = (
        # the last structural change to the package model
        ('main', '0026_auto__add_field_package_packager_str__add_field_package_packager'),
    )

    def forwards(self, orm):
        "Migrate the flat license text to a seperate relation."
        for pkg in orm['main.Package'].objects.all():
            licenses = pkg.license.split(u', ')
            for license in licenses:
                pkg.licenses.create(name=license)

    def backwards(self, orm):
        for pkg in orm['main.Package'].objects.all():
            pkg.license = u', '.join([l.name for l in pkg.licenses.all()])
            pkg.save()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.arch': {
            'Meta': {'ordering': "['name']", 'object_name': 'Arch', 'db_table': "'arches'"},
            'agnostic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'main.package': {
            'Meta': {'ordering': "('pkgname',)", 'object_name': 'Package', 'db_table': "'packages'"},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': "orm['main.Arch']"}),
            'build_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'compressed_size': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'files_last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'flag_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installed_size': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'packager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'packager_str': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkgdesc': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'pkgname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': "orm['main.Repo']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'main.repo': {
            'Meta': {'ordering': "['name']", 'object_name': 'Repo', 'db_table': "'repos'"},
            'bugs_project': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'svn_root': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'testing': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'packages.license': {
            'Meta': {'object_name': 'License'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'licenses'", 'to': "orm['main.Package']"})
        },
        'packages.packagegroup': {
            'Meta': {'object_name': 'PackageGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Package']"})
        },
        'packages.packagerelation': {
            'Meta': {'unique_together': "(('pkgbase', 'user', 'type'),)", 'object_name': 'PackageRelation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'package_relations'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['packages']

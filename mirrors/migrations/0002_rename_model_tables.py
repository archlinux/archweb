# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ('main', '0030_move_mirror_models'),
    )

    mirror_apps = [ 'mirror', 'mirrorprotocol', 'mirrorurl', 'mirrorrsync' ]

    def forwards(self, orm):
        db.rename_table('main_mirror', 'mirrors_mirror')
        db.rename_table('main_mirrorurl', 'mirrors_mirrorurl')
        db.rename_table('main_mirrorrsync', 'mirrors_mirrorrsync')
        db.rename_table('main_mirrorprotocol', 'mirrors_mirrorprotocol')

        if not db.dry_run:
            ct = orm['contenttypes.ContentType'].objects
            ct.filter(app_label='main', model__in=self.mirror_apps).update(
                    app_label='mirrors')

    def backwards(self, orm):
        db.rename_table('mirrors_mirror', 'main_mirror')
        db.rename_table('mirrors_mirrorurl', 'main_mirrorurl')
        db.rename_table('mirrors_mirrorrsync', 'main_mirrorrsync')
        db.rename_table('mirrors_mirrorprotocol', 'main_mirrorprotocol')

        if not db.dry_run:
            ct = orm['contenttypes.ContentType'].objects
            ct.filter(app_label='mirrors', model__in=self.mirror_apps).update(
                    app_label='main')

    models = {
        'mirrors.mirror': {
            'Meta': {'ordering': "('country', 'name')", 'object_name': 'Mirror'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admin_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isos': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rsync_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'rsync_user': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'tier': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'upstream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mirrors.Mirror']", 'null': 'True'})
        },
        'mirrors.mirrorprotocol': {
            'Meta': {'object_name': 'MirrorProtocol'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        'mirrors.mirrorrsync': {
            'Meta': {'object_name': 'MirrorRsync'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'mirror': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rsync_ips'", 'to': "orm['mirrors.Mirror']"})
        },
        'mirrors.mirrorurl': {
            'Meta': {'object_name': 'MirrorUrl'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mirror': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': "orm['mirrors.Mirror']"}),
            'protocol': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': "orm['mirrors.MirrorProtocol']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['mirrors']

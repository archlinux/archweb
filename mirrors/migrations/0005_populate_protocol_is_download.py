# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        orm.MirrorProtocol.objects.filter(protocol__iexact='ftp').update(is_download=True)
        orm.MirrorProtocol.objects.filter(protocol__iexact='http').update(is_download=True)
        orm.MirrorProtocol.objects.filter(protocol__iexact='rsync').update(is_download=False)

    def backwards(self, orm):
        pass

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
        'mirrors.mirrorlog': {
            'Meta': {'object_name': 'MirrorLog'},
            'check_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'duration': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_success': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'url': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': "orm['mirrors.MirrorUrl']"})
        },
        'mirrors.mirrorprotocol': {
            'Meta': {'object_name': 'MirrorProtocol'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_download': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
        }
    }

    complete_apps = ['mirrors']

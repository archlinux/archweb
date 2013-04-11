# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        if db.backend_name == 'postgres':
            # For PostgreSQL, because it uses the 'inet' type and not a varchar
            # column, we need to add an explict 'USING' cast to the SQL
            # statement. We then execute the alter_column as well to ensure any
            # of the other side-effects happen.
            db.execute('ALTER TABLE "mirrors_mirrorrsync" ALTER COLUMN "ip" TYPE inet USING "ip"::inet')
        db.alter_column(u'mirrors_mirrorrsync', 'ip', self.gf('mirrors.fields.IPNetworkField')(max_length=44))

    def backwards(self, orm):
        db.alter_column(u'mirrors_mirrorrsync', 'ip', self.gf('django.db.models.fields.CharField')(max_length=44))

    models = {
        u'mirrors.checklocation': {
            'Meta': {'ordering': "('hostname', 'source_ip')", 'object_name': 'CheckLocation'},
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_ip': ('django.db.models.fields.GenericIPAddressField', [], {'unique': 'True', 'max_length': '39'})
        },
        u'mirrors.mirror': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Mirror'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'admin_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'alternate_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isos': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rsync_password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'rsync_user': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'tier': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'upstream': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mirrors.Mirror']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        u'mirrors.mirrorlog': {
            'Meta': {'object_name': 'MirrorLog'},
            'check_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'duration': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_success': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'null': 'True', 'to': u"orm['mirrors.CheckLocation']"}),
            'url': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['mirrors.MirrorUrl']"})
        },
        u'mirrors.mirrorprotocol': {
            'Meta': {'ordering': "('protocol',)", 'object_name': 'MirrorProtocol'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_download': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        u'mirrors.mirrorrsync': {
            'Meta': {'object_name': 'MirrorRsync'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('mirrors.fields.IPNetworkField', [], {'max_length': '44'}),
            'mirror': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rsync_ips'", 'to': u"orm['mirrors.Mirror']"})
        },
        u'mirrors.mirrorurl': {
            'Meta': {'object_name': 'MirrorUrl'},
            'country': ('django_countries.fields.CountryField', [], {'db_index': 'True', 'max_length': '2', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'has_ipv4': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_ipv6': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mirror': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': u"orm['mirrors.Mirror']"}),
            'protocol': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'on_delete': 'models.PROTECT', 'to': u"orm['mirrors.MirrorProtocol']"}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['mirrors']

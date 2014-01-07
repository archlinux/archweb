# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.delete_column(u'releng_release', 'torrent_infohash')
        db.delete_column(u'releng_release', 'file_size')

    def backwards(self, orm):
        db.add_column(u'releng_release', 'torrent_infohash',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=40, blank=True),
                      keep_default=False)
        db.add_column(u'releng_release', 'file_size',
                      self.gf('main.fields.PositiveBigIntegerField')(null=True, blank=True),
                      keep_default=False)

    models = {
        u'releng.architecture': {
            'Meta': {'object_name': 'Architecture'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.bootloader': {
            'Meta': {'object_name': 'Bootloader'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.boottype': {
            'Meta': {'object_name': 'BootType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.clockchoice': {
            'Meta': {'object_name': 'ClockChoice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.filesystem': {
            'Meta': {'object_name': 'Filesystem'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.hardwaretype': {
            'Meta': {'object_name': 'HardwareType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.installtype': {
            'Meta': {'object_name': 'InstallType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.iso': {
            'Meta': {'object_name': 'Iso'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'removed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        u'releng.isotype': {
            'Meta': {'object_name': 'IsoType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.module': {
            'Meta': {'object_name': 'Module'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.release': {
            'Meta': {'ordering': "('-release_date', '-version')", 'object_name': 'Release'},
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'kernel_version': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'md5_sum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'sha1_sum': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'torrent_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'releng.source': {
            'Meta': {'object_name': 'Source'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'releng.test': {
            'Meta': {'object_name': 'Test'},
            'architecture': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.Architecture']"}),
            'boot_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.BootType']"}),
            'bootloader': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.Bootloader']"}),
            'clock_choice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.ClockChoice']"}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'filesystem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.Filesystem']"}),
            'hardware_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.HardwareType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'install_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.InstallType']"}),
            'ip_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39'}),
            'iso': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.Iso']"}),
            'iso_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.IsoType']"}),
            'modules': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['releng.Module']", 'null': 'True', 'blank': 'True'}),
            'rollback_filesystem': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rollback_test_set'", 'null': 'True', 'to': u"orm['releng.Filesystem']"}),
            'rollback_modules': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'rollback_test_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['releng.Module']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['releng.Source']"}),
            'success': ('django.db.models.fields.BooleanField', [], {}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        }
    }

    complete_apps = ['releng']

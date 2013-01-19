# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Release.file_size'
        db.add_column('releng_release', 'file_size',
                      self.gf('main.fields.PositiveBigIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Release.torrent_data'
        db.add_column('releng_release', 'torrent_data',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Release.file_size'
        db.delete_column('releng_release', 'file_size')

        # Deleting field 'Release.torrent_data'
        db.delete_column('releng_release', 'torrent_data')


    models = {
        'releng.architecture': {
            'Meta': {'object_name': 'Architecture'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.bootloader': {
            'Meta': {'object_name': 'Bootloader'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.boottype': {
            'Meta': {'object_name': 'BootType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.clockchoice': {
            'Meta': {'object_name': 'ClockChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.filesystem': {
            'Meta': {'object_name': 'Filesystem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.hardwaretype': {
            'Meta': {'object_name': 'HardwareType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.installtype': {
            'Meta': {'object_name': 'InstallType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.iso': {
            'Meta': {'object_name': 'Iso'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'removed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'releng.isotype': {
            'Meta': {'object_name': 'IsoType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.module': {
            'Meta': {'object_name': 'Module'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.release': {
            'Meta': {'ordering': "('-release_date', '-version')", 'object_name': 'Release'},
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'file_size': ('main.fields.PositiveBigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'kernel_version': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'torrent_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'torrent_infohash': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'releng.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'releng.test': {
            'Meta': {'object_name': 'Test'},
            'architecture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.Architecture']"}),
            'boot_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.BootType']"}),
            'bootloader': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.Bootloader']"}),
            'clock_choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.ClockChoice']"}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'filesystem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.Filesystem']"}),
            'hardware_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.HardwareType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'install_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.InstallType']"}),
            'ip_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39'}),
            'iso': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.Iso']"}),
            'iso_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.IsoType']"}),
            'modules': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['releng.Module']", 'null': 'True', 'blank': 'True'}),
            'rollback_filesystem': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rollback_test_set'", 'null': 'True', 'to': "orm['releng.Filesystem']"}),
            'rollback_modules': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'rollback_test_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['releng.Module']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['releng.Source']"}),
            'success': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        }
    }

    complete_apps = ['releng']
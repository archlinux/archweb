# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Iso'
        db.create_table('releng_iso', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('releng', ['Iso'])

        # Adding model 'Architecture'
        db.create_table('releng_architecture', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['Architecture'])

        # Adding model 'IsoType'
        db.create_table('releng_isotype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['IsoType'])

        # Adding model 'BootType'
        db.create_table('releng_boottype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['BootType'])

        # Adding model 'HardwareType'
        db.create_table('releng_hardwaretype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['HardwareType'])

        # Adding model 'InstallType'
        db.create_table('releng_installtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['InstallType'])

        # Adding model 'Source'
        db.create_table('releng_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['Source'])

        # Adding model 'ClockChoice'
        db.create_table('releng_clockchoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['ClockChoice'])

        # Adding model 'Filesystem'
        db.create_table('releng_filesystem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['Filesystem'])

        # Adding model 'Module'
        db.create_table('releng_module', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['Module'])

        # Adding model 'Bootloader'
        db.create_table('releng_bootloader', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('releng', ['Bootloader'])

        # Adding model 'Test'
        db.create_table('releng_test', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('user_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('iso', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.Iso'])),
            ('architecture', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.Architecture'])),
            ('iso_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.IsoType'])),
            ('boot_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.BootType'])),
            ('hardware_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.HardwareType'])),
            ('install_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.InstallType'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.Source'])),
            ('clock_choice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.ClockChoice'])),
            ('filesystem', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.Filesystem'])),
            ('bootloader', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['releng.Bootloader'])),
            ('rollback_filesystem', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='rollback_test_set', null=True, to=orm['releng.Filesystem'])),
            ('success', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('comments', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('releng', ['Test'])

        # Adding M2M table for field modules on 'Test'
        db.create_table('releng_test_modules', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('test', models.ForeignKey(orm['releng.test'], null=False)),
            ('module', models.ForeignKey(orm['releng.module'], null=False))
        ))
        db.create_unique('releng_test_modules', ['test_id', 'module_id'])

        # Adding M2M table for field rollback_modules on 'Test'
        db.create_table('releng_test_rollback_modules', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('test', models.ForeignKey(orm['releng.test'], null=False)),
            ('module', models.ForeignKey(orm['releng.module'], null=False))
        ))
        db.create_unique('releng_test_rollback_modules', ['test_id', 'module_id'])


    def backwards(self, orm):
        
        # Deleting model 'Iso'
        db.delete_table('releng_iso')

        # Deleting model 'Architecture'
        db.delete_table('releng_architecture')

        # Deleting model 'IsoType'
        db.delete_table('releng_isotype')

        # Deleting model 'BootType'
        db.delete_table('releng_boottype')

        # Deleting model 'HardwareType'
        db.delete_table('releng_hardwaretype')

        # Deleting model 'InstallType'
        db.delete_table('releng_installtype')

        # Deleting model 'Source'
        db.delete_table('releng_source')

        # Deleting model 'ClockChoice'
        db.delete_table('releng_clockchoice')

        # Deleting model 'Filesystem'
        db.delete_table('releng_filesystem')

        # Deleting model 'Module'
        db.delete_table('releng_module')

        # Deleting model 'Bootloader'
        db.delete_table('releng_bootloader')

        # Deleting model 'Test'
        db.delete_table('releng_test')

        # Removing M2M table for field modules on 'Test'
        db.delete_table('releng_test_modules')

        # Removing M2M table for field rollback_modules on 'Test'
        db.delete_table('releng_test_rollback_modules')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
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

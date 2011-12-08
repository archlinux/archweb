# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FlagRequest'
        db.create_table('packages_flagrequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('user_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('pkgbase', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('repo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Repo'])),
            ('num_packages', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_spam', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_legitimate', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('packages', ['FlagRequest'])

        if db.backend_name == 'mysql':
            # stupid f#$%ing storage of IP address as a 15 character type
            db.execute("ALTER TABLE packages_flagrequest "
                    "MODIFY ip_address char(39) NOT NULL")


    def backwards(self, orm):
        # Deleting model 'FlagRequest'
        db.delete_table('packages_flagrequest')


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
            'Meta': {'ordering': "('pkgname',)", 'unique_together': "(('pkgname', 'repo', 'arch'),)", 'object_name': 'Package', 'db_table': "'packages'"},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': "orm['main.Arch']"}),
            'build_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'compressed_size': ('main.fields.PositiveBigIntegerField', [], {}),
            'epoch': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'files_last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'flag_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installed_size': ('main.fields.PositiveBigIntegerField', [], {}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {}),
            'packager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'packager_str': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pgp_signature': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkgdesc': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'pkgname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': "orm['main.Repo']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'main.repo': {
            'Meta': {'ordering': "['name']", 'object_name': 'Repo', 'db_table': "'repos'"},
            'bugs_category': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'bugs_project': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'staging': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'svn_root': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'testing': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'packages.conflict': {
            'Meta': {'ordering': "['name']", 'object_name': 'Conflict'},
            'comparison': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'conflicts'", 'to': "orm['main.Package']"}),
            'version': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
        },
        'packages.flagrequest': {
            'Meta': {'object_name': 'FlagRequest'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'is_legitimate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_spam': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'num_packages': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Repo']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'})
        },
        'packages.license': {
            'Meta': {'ordering': "['name']", 'object_name': 'License'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'licenses'", 'to': "orm['main.Package']"})
        },
        'packages.packagegroup': {
            'Meta': {'object_name': 'PackageGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['main.Package']"})
        },
        'packages.packagerelation': {
            'Meta': {'unique_together': "(('pkgbase', 'user', 'type'),)", 'object_name': 'PackageRelation'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'package_relations'", 'to': "orm['auth.User']"})
        },
        'packages.provision': {
            'Meta': {'ordering': "['name']", 'object_name': 'Provision'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'provides'", 'to': "orm['main.Package']"}),
            'version': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
        },
        'packages.replacement': {
            'Meta': {'ordering': "['name']", 'object_name': 'Replacement'},
            'comparison': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'replaces'", 'to': "orm['main.Package']"}),
            'version': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'})
        },
        'packages.signoff': {
            'Meta': {'object_name': 'Signoff'},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Arch']"}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'epoch': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Repo']"}),
            'revoked': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'package_signoffs'", 'to': "orm['auth.User']"})
        },
        'packages.signoffspecification': {
            'Meta': {'object_name': 'SignoffSpecification'},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Arch']"}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'epoch': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'known_bad': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Repo']"}),
            'required': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        }
    }

    complete_apps = ['packages']

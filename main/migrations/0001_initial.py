# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'PackageDepend'
        db.create_table('package_depends', (
            ('id', orm['main.PackageDepend:id']),
            ('pkg', orm['main.PackageDepend:pkg']),
            ('depname', orm['main.PackageDepend:depname']),
            ('depvcmp', orm['main.PackageDepend:depvcmp']),
        ))
        db.send_create_signal('main', ['PackageDepend'])
        
        # Adding model 'Press'
        db.create_table('press', (
            ('id', orm['main.Press:id']),
            ('name', orm['main.Press:name']),
            ('url', orm['main.Press:url']),
        ))
        db.send_create_signal('main', ['Press'])
        
        # Adding model 'MirrorUrl'
        db.create_table('main_mirrorurl', (
            ('id', orm['main.MirrorUrl:id']),
            ('url', orm['main.MirrorUrl:url']),
            ('protocol', orm['main.MirrorUrl:protocol']),
            ('mirror', orm['main.MirrorUrl:mirror']),
        ))
        db.send_create_signal('main', ['MirrorUrl'])
        
        # Adding model 'MirrorRsync'
        db.create_table('main_mirrorrsync', (
            ('id', orm['main.MirrorRsync:id']),
            ('hostname', orm['main.MirrorRsync:hostname']),
            ('ip', orm['main.MirrorRsync:ip']),
            ('mirror', orm['main.MirrorRsync:mirror']),
        ))
        db.send_create_signal('main', ['MirrorRsync'])
        
        # Adding model 'AltForum'
        db.create_table('alt_forums', (
            ('id', orm['main.AltForum:id']),
            ('language', orm['main.AltForum:language']),
            ('url', orm['main.AltForum:url']),
            ('name', orm['main.AltForum:name']),
        ))
        db.send_create_signal('main', ['AltForum'])
        
        # Adding model 'Signoff'
        db.create_table('main_signoff', (
            ('id', orm['main.Signoff:id']),
            ('pkg', orm['main.Signoff:pkg']),
            ('pkgver', orm['main.Signoff:pkgver']),
            ('pkgrel', orm['main.Signoff:pkgrel']),
            ('packager', orm['main.Signoff:packager']),
        ))
        db.send_create_signal('main', ['Signoff'])
        
        # Adding model 'UserProfile'
        db.create_table('user_profiles', (
            ('id', orm['main.UserProfile:id']),
            ('notify', orm['main.UserProfile:notify']),
            ('alias', orm['main.UserProfile:alias']),
            ('public_email', orm['main.UserProfile:public_email']),
            ('other_contact', orm['main.UserProfile:other_contact']),
            ('website', orm['main.UserProfile:website']),
            ('yob', orm['main.UserProfile:yob']),
            ('location', orm['main.UserProfile:location']),
            ('languages', orm['main.UserProfile:languages']),
            ('interests', orm['main.UserProfile:interests']),
            ('occupation', orm['main.UserProfile:occupation']),
            ('roles', orm['main.UserProfile:roles']),
            ('favorite_distros', orm['main.UserProfile:favorite_distros']),
            ('picture', orm['main.UserProfile:picture']),
            ('user', orm['main.UserProfile:user']),
        ))
        db.send_create_signal('main', ['UserProfile'])
        
        # Adding model 'Arch'
        db.create_table('arches', (
            ('id', orm['main.Arch:id']),
            ('name', orm['main.Arch:name']),
        ))
        db.send_create_signal('main', ['Arch'])
        
        # Adding model 'PackageFile'
        db.create_table('package_files', (
            ('id', orm['main.PackageFile:id']),
            ('pkg', orm['main.PackageFile:pkg']),
            ('path', orm['main.PackageFile:path']),
        ))
        db.send_create_signal('main', ['PackageFile'])
        
        # Adding model 'Todolist'
        db.create_table('todolists', (
            ('id', orm['main.Todolist:id']),
            ('creator', orm['main.Todolist:creator']),
            ('name', orm['main.Todolist:name']),
            ('description', orm['main.Todolist:description']),
            ('date_added', orm['main.Todolist:date_added']),
        ))
        db.send_create_signal('main', ['Todolist'])
        
        # Adding model 'TodolistPkg'
        db.create_table('todolist_pkgs', (
            ('id', orm['main.TodolistPkg:id']),
            ('list', orm['main.TodolistPkg:list']),
            ('pkg', orm['main.TodolistPkg:pkg']),
            ('complete', orm['main.TodolistPkg:complete']),
        ))
        db.send_create_signal('main', ['TodolistPkg'])
        
        # Adding model 'Donor'
        db.create_table('donors', (
            ('id', orm['main.Donor:id']),
            ('name', orm['main.Donor:name']),
        ))
        db.send_create_signal('main', ['Donor'])
        
        # Adding model 'Package'
        db.create_table('packages', (
            ('id', orm['main.Package:id']),
            ('repo', orm['main.Package:repo']),
            ('arch', orm['main.Package:arch']),
            ('maintainer', orm['main.Package:maintainer']),
            ('needupdate', orm['main.Package:needupdate']),
            ('pkgname', orm['main.Package:pkgname']),
            ('pkgbase', orm['main.Package:pkgbase']),
            ('pkgver', orm['main.Package:pkgver']),
            ('pkgrel', orm['main.Package:pkgrel']),
            ('pkgdesc', orm['main.Package:pkgdesc']),
            ('url', orm['main.Package:url']),
            ('last_update', orm['main.Package:last_update']),
            ('license', orm['main.Package:license']),
        ))
        db.send_create_signal('main', ['Package'])
        
        # Adding model 'Repo'
        db.create_table('repos', (
            ('id', orm['main.Repo:id']),
            ('name', orm['main.Repo:name']),
        ))
        db.send_create_signal('main', ['Repo'])
        
        # Adding model 'Mirror'
        db.create_table('main_mirror', (
            ('id', orm['main.Mirror:id']),
            ('name', orm['main.Mirror:name']),
            ('country', orm['main.Mirror:country']),
            ('admin_email', orm['main.Mirror:admin_email']),
            ('notes', orm['main.Mirror:notes']),
            ('public', orm['main.Mirror:public']),
            ('active', orm['main.Mirror:active']),
            ('isos', orm['main.Mirror:isos']),
        ))
        db.send_create_signal('main', ['Mirror'])
        
        # Adding model 'MirrorProtocol'
        db.create_table('main_mirrorprotocol', (
            ('id', orm['main.MirrorProtocol:id']),
            ('protocol', orm['main.MirrorProtocol:protocol']),
        ))
        db.send_create_signal('main', ['MirrorProtocol'])
        
        # Adding model 'ExternalProject'
        db.create_table('main_externalproject', (
            ('id', orm['main.ExternalProject:id']),
            ('url', orm['main.ExternalProject:url']),
            ('name', orm['main.ExternalProject:name']),
            ('description', orm['main.ExternalProject:description']),
        ))
        db.send_create_signal('main', ['ExternalProject'])
        
        # Adding model 'News'
        db.create_table('news', (
            ('id', orm['main.News:id']),
            ('author', orm['main.News:author']),
            ('postdate', orm['main.News:postdate']),
            ('title', orm['main.News:title']),
            ('content', orm['main.News:content']),
        ))
        db.send_create_signal('main', ['News'])
        
        # Adding ManyToManyField 'UserProfile.allowed_repos'
        db.create_table('user_profiles_allowed_repos', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm.UserProfile, null=False)),
            ('repo', models.ForeignKey(orm.Repo, null=False))
        ))
        
        # Creating unique_together for [list, pkg] on TodolistPkg.
        db.create_unique('todolist_pkgs', ['list_id', 'pkg_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [list, pkg] on TodolistPkg.
        db.delete_unique('todolist_pkgs', ['list_id', 'pkg_id'])
        
        # Deleting model 'PackageDepend'
        db.delete_table('package_depends')
        
        # Deleting model 'Press'
        db.delete_table('press')
        
        # Deleting model 'MirrorUrl'
        db.delete_table('main_mirrorurl')
        
        # Deleting model 'MirrorRsync'
        db.delete_table('main_mirrorrsync')
        
        # Deleting model 'AltForum'
        db.delete_table('alt_forums')
        
        # Deleting model 'Signoff'
        db.delete_table('main_signoff')
        
        # Deleting model 'UserProfile'
        db.delete_table('user_profiles')
        
        # Deleting model 'Arch'
        db.delete_table('arches')
        
        # Deleting model 'PackageFile'
        db.delete_table('package_files')
        
        # Deleting model 'Todolist'
        db.delete_table('todolists')
        
        # Deleting model 'TodolistPkg'
        db.delete_table('todolist_pkgs')
        
        # Deleting model 'Donor'
        db.delete_table('donors')
        
        # Deleting model 'Package'
        db.delete_table('packages')
        
        # Deleting model 'Repo'
        db.delete_table('repos')
        
        # Deleting model 'Mirror'
        db.delete_table('main_mirror')
        
        # Deleting model 'MirrorProtocol'
        db.delete_table('main_mirrorprotocol')
        
        # Deleting model 'ExternalProject'
        db.delete_table('main_externalproject')
        
        # Deleting model 'News'
        db.delete_table('news')
        
        # Dropping ManyToManyField 'UserProfile.allowed_repos'
        db.delete_table('user_profiles_allowed_repos')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.altforum': {
            'Meta': {'db_table': "'alt_forums'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.arch': {
            'Meta': {'db_table': "'arches'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'main.donor': {
            'Meta': {'db_table': "'donors'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'main.externalproject': {
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'main.mirror': {
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'admin_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isos': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'})
        },
        'main.mirrorprotocol': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'})
        },
        'main.mirrorrsync': {
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'mirror': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rsync_ips'", 'to': "orm['main.Mirror']"})
        },
        'main.mirrorurl': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mirror': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': "orm['main.Mirror']"}),
            'protocol': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'urls'", 'to': "orm['main.MirrorProtocol']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.news': {
            'Meta': {'db_table': "'news'"},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'news_author'", 'to': "orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'postdate': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.package': {
            'Meta': {'db_table': "'packages'"},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': "orm['main.Arch']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'maintainer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'maintained_packages'", 'to': "orm['auth.User']"}),
            'needupdate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'pkgdesc': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'to': "orm['main.Repo']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.packagedepend': {
            'Meta': {'db_table': "'package_depends'"},
            'depname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'depvcmp': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']"})
        },
        'main.packagefile': {
            'Meta': {'db_table': "'package_files'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']"})
        },
        'main.press': {
            'Meta': {'db_table': "'press'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.repo': {
            'Meta': {'db_table': "'repos'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'main.signoff': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'packager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']"}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.todolist': {
            'Meta': {'db_table': "'todolists'"},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'date_added': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.todolistpkg': {
            'Meta': {'unique_together': "(('list', 'pkg'),)", 'db_table': "'todolist_pkgs'"},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Todolist']"}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']"})
        },
        'main.userprofile': {
            'Meta': {'db_table': "'user_profiles'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'allowed_repos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Repo']", 'blank': 'True'}),
            'favorite_distros': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interests': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'languages': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'notify': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'other_contact': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'picture': ('django.db.models.fields.files.FileField', [], {'default': "'devs/silhouette.png'", 'max_length': '100'}),
            'public_email': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'roles': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userprofile_user'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'yob': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['main']

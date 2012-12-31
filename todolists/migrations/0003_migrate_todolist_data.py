# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    depends_on = (
        ('main', '0045_add_todolist_date_added_index'),
        ('main', '0053_auto__add_field_package_pgp_signature'),
    )

    def forwards(self, orm):
        list_id_map = {}
        list_added = {}
        # start by converting the todo lists themselves
        for old in orm['main.Todolist'].objects.all().order_by('id'):
            new = orm.Todolist.objects.create(name=old.name, old_id=old.id,
                    description=old.description, created=old.date_added,
                    last_modified=old.date_added, creator_id=old.creator_id)
            # set the 'raw' field to something useful
            pkgnames = orm['main.Package'].objects.values_list('pkgname',
                    flat=True).distinct().order_by('pkgname').filter(
                    todolistpkg__list_id=old.id)
            pkgname_text = '\n'.join(pkgnames)
            orm.Todolist.objects.filter(id=new.id).update(raw=pkgname_text)
            list_id_map[old.id] = new.id
            list_added[old.id] = old.date_added

        # 1 and 0 come from TodolistPackage.COMPLETE, INCOMPLETE
        get_status = lambda v: 1 if v is True else 0
        # next, loop each old todolist package, creating a new one
        for old in orm['main.TodolistPkg'].objects.all().select_related(
                'pkg').order_by('id'):
            pkg = old.pkg
            new_list_id = list_id_map[old.list_id]
            orm.TodolistPackage.objects.create(todolist_id=new_list_id,
                    pkg=pkg, pkgname=pkg.pkgname, pkgbase=pkg.pkgbase,
                    arch_id=pkg.arch_id, repo_id=pkg.repo_id,
                    status=get_status(old.complete),
                    created=list_added[old.list_id])

    def backwards(self, orm):
        #orm.Todolist.objects.all().delete()
        #orm.TodolistPackage.objects.all().delete()
        pass


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
            'Meta': {'ordering': "('name',)", 'object_name': 'Arch', 'db_table': "'arches'"},
            'agnostic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'main.donor': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Donor', 'db_table': "'donors'"},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'main.package': {
            'Meta': {'ordering': "('pkgname',)", 'unique_together': "(('pkgname', 'repo', 'arch'),)", 'object_name': 'Package', 'db_table': "'packages'"},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'on_delete': 'models.PROTECT', 'to': "orm['main.Arch']"}),
            'build_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'compressed_size': ('main.fields.PositiveBigIntegerField', [], {}),
            'epoch': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'files_last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'flag_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installed_size': ('main.fields.PositiveBigIntegerField', [], {}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'packager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'packager_str': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pgp_signature': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'pkgdesc': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'pkgname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgrel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgver': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packages'", 'on_delete': 'models.PROTECT', 'to': "orm['main.Repo']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'main.packagefile': {
            'Meta': {'object_name': 'PackageFile', 'db_table': "'package_files'"},
            'directory': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_directory': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']"})
        },
        'main.repo': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Repo', 'db_table': "'repos'"},
            'bugs_category': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'bugs_project': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'staging': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'svn_root': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'testing': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'main.todolist': {
            'Meta': {'object_name': 'Todolist', 'db_table': "'todolists'"},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'on_delete': 'models.PROTECT'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.todolistpkg': {
            'Meta': {'unique_together': "(('list', 'pkg'),)", 'object_name': 'TodolistPkg', 'db_table': "'todolist_pkgs'"},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Todolist']"}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']"})
        },
        'todolists.todolist': {
            'Meta': {'object_name': 'Todolist'},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_todolists'", 'on_delete': 'models.PROTECT', 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True'}),
            'raw': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'todolists.todolistpackage': {
            'Meta': {'unique_together': "(('todolist', 'pkgname', 'arch'),)", 'object_name': 'TodolistPackage'},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Arch']"}),
            'comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pkg': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Package']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'pkgbase': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pkgname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'repo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Repo']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'todolist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['todolists.Todolist']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        }
    }

    complete_apps = ['main', 'todolists']
    symmetrical = True

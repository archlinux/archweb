from django.db import models
from django.contrib.auth.models import User
from archweb_dev.packages.models import Package

class TodolistManager(models.Manager):
	def get_incomplete(self):
		results = []
		for l in self.all().order_by('-date_added'):
			if TodolistPkg.objects.filter(list=l.id).filter(complete=False).count() > 0:
				results.append(l)
		return results

class Todolist(models.Model):
	id = models.AutoField(primary_key=True)
	creator = models.ForeignKey(User)
	name = models.CharField(maxlength=255)
	description = models.TextField()
	date_added = models.DateField(auto_now_add=True)
	objects = TodolistManager()
	class Meta:
		db_table = 'todolists'

class TodolistPkg(models.Model):
	id = models.AutoField(primary_key=True)
	list = models.ForeignKey(Todolist)
	pkg = models.ForeignKey(Package)
	complete = models.BooleanField(default=False)
	class Meta:
		db_table = 'todolists_pkgs'
		unique_together = (('list','pkg'),)


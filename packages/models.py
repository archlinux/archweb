from django.db import models
from django.contrib.auth.models import User
import re

class PackageManager(models.Manager):
	def get_flag_stats(self):
		results = []
		# first the orphans
		unflagged = self.filter(maintainer=0).count()
		flagged   = self.filter(maintainer=0).filter(needupdate=True).count()
		results.append((User(id=0,first_name='Orphans'), unflagged, flagged))
		# now the rest
		for maint in User.objects.all().order_by('first_name'):
			unflagged = self.filter(maintainer=maint.id).count()
			flagged   = self.filter(maintainer=maint.id).filter(needupdate=True).count()
			results.append((maint, unflagged, flagged))
		return results

class Category(models.Model):
	id = models.AutoField(primary_key=True)
	category = models.CharField(maxlength=255)
	class Meta:
		db_table = 'categories'
		verbose_name_plural = 'categories'

class Repo(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(maxlength=255)
	class Meta:
		db_table = 'repos'
	def last_update(self):
		try:
			latest = Package.objects.filter(repo__name__exact=self.name).order_by('-last_update')[0]
			return latest.last_update
		except IndexError:
			return "N/A"

class Package(models.Model):
	id = models.AutoField(primary_key=True)
	repo = models.ForeignKey(Repo)
	maintainer = models.ForeignKey(User)
	category = models.ForeignKey(Category)
	needupdate = models.BooleanField(default=False)
	pkgname = models.CharField(maxlength=255)
	pkgver = models.CharField(maxlength=255)
	pkgrel = models.CharField(maxlength=255)
	pkgdesc = models.CharField(maxlength=255)
	url = models.URLField()
	sources = models.TextField()
	depends = models.TextField()
	last_update = models.DateTimeField(null=True, blank=True)
	objects = PackageManager()
	class Meta:
		db_table = 'packages'
		get_latest_by = 'last_update'

	def get_absolute_url(self):
		return '/packages/%i/' % self.id

	def depends_urlize(self):
		urls = ''
		for dep in self.depends.split(' '):
			# shave off any version qualifiers
			nameonly = re.match(r"([a-z0-9-]+)", dep).group(1)
			try:
				p = Package.objects.filter(pkgname=nameonly)[0]
			except IndexError:
				# couldn't find a package in the DB -- it might be a virtual depend
				urls = urls + '<li>' + dep + '</li>'
				continue
			url = '<li><a href="/packages/' + str(p.id) + '">' + dep + '</a></li>'
			urls = urls + url
		return urls

	def sources_urlize(self):
		urls = ''
		for source in self.sources.split(' '):
			if re.search('://', source):
				url = '<li><a href="' + source + '">' + source + '</a></li>'
			else:
				url = '<li>' + source + '</li>'
			urls = urls + url
		return urls

class PackageFile(models.Model):
	id = models.AutoField(primary_key=True)
	pkg = models.ForeignKey(Package)
	path = models.CharField(maxlength=255)
	class Meta:
		db_table = 'packages_files'


from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
import re

###########################
### User Profile Class ####
###########################
class UserProfile(models.Model):
    id = models.AutoField(primary_key=True) # not technically needed
    notify = models.BooleanField("Send notifications", default=True, help_text="When enabled, user will recieve 'flag out of date' notifications")
    alias = models.CharField(core=True, maxlength=50, help_text="Required field")
    public_email = models.CharField(core=True, maxlength=50, help_text="Required field")
    other_contact = models.CharField(maxlength=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    yob = models.IntegerField(null=True, blank=True)
    location = models.CharField(maxlength=50, null=True, blank=True)
    languages = models.CharField(maxlength=50, null=True, blank=True)
    interests = models.CharField(maxlength=255, null=True, blank=True)
    occupation = models.CharField(maxlength=50, null=True, blank=True)
    roles = models.CharField(maxlength=255, null=True, blank=True)
    favorite_distros = models.CharField(maxlength=255, null=True, blank=True)
    picture = models.FileField(upload_to='devs', default='devs/silhouette.png')
    user = models.ForeignKey(
        User, related_name='userprofile_user',  
        edit_inline=models.STACKED, num_in_admin=1, 
        min_num_in_admin=1, max_num_in_admin=1, 
        num_extra_on_change=0, unique=True)
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Additional Profile Data'
        verbose_name_plural = 'Additional Profile Data'


#######################
### Manager Classes ###
#######################
class TodolistManager(models.Manager):
    def get_incomplete(self):
        results = []
        for l in self.all().order_by('-date_added'):
            if TodolistPkg.objects.filter(list=l.id).filter(
                complete=False).count() > 0:
                results.append(l)
        return results

class PackageManager(models.Manager):
    def get_flag_stats(self):
        results = []
        # first the orphans
        noflag = self.filter(maintainer=0).count()
        flagged = self.filter(maintainer=0).filter(
                    needupdate=True).exclude(
                        repo__name__iexact='testing').count()
        results.append(
            (User(id=0,first_name='Orphans'), noflag, flagged))
        # now the rest
        for maint in User.objects.all().order_by('first_name'):
            noflag = self.filter(maintainer=maint.id).count()
            flagged = self.filter(maintainer=maint.id).filter(
                    needupdate=True).exclude(
                        repo__name__iexact='testing').count()
            results.append((maint, noflag, flagged))
        return results


#############################
### General Model Classes ###
#############################
class Mirror(models.Model):
    id = models.AutoField(primary_key=True)
    domain = models.CharField(maxlength=255)
    country = models.CharField(maxlength=255)
    url = models.CharField(maxlength=255)
    protocol_list = models.CharField(maxlength=255, null=True, blank=True)
    admin_email = models.CharField(maxlength=255, null=True, blank=True)
    def __str__(self):
        return self.domain
    class Meta:
        db_table = 'mirrors'
    class Admin:
        list_display = ('domain', 'country')
        list_filter = ('country',)
        ordering = ['domain']
        search_fields = ('domain')
        pass

class Press(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(maxlength=255)
    url = models.CharField(maxlength=255)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'press'
        verbose_name_plural = 'press'
    class Admin:
        ordering = ['name']
        search_fields = ('name')
        pass

class AltForum(models.Model):
    id = models.AutoField(primary_key=True)
    language = models.CharField(maxlength=255)
    url = models.CharField(maxlength=255)
    name = models.CharField(maxlength=255)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'alt_forums'
        verbose_name = 'AltForum'
    class Admin:
        list_display = ('language', 'name')
        list_filter = ('language',)
        ordering = ['name']
        search_fields = ('name')
        pass

class Donor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(maxlength=255)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'donors'
    class Admin:
        ordering = ['name']
        search_fields = ('name')
        pass

class News(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, related_name='news_author')
    postdate = models.DateField(auto_now_add=True)
    title = models.CharField(maxlength=255)
    content = models.TextField()
    def __str__(self):
        return self.title
    class Meta:
        db_table = 'news'
        verbose_name_plural = 'news'
        get_latest_by = 'postdate'
        ordering = ['-postdate', '-id']

    def get_absolute_url(self):
        return '/news/%i/' % self.id

class Arch(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(maxlength=255,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'arches'
        ordering = ['name']
        verbose_name_plural = 'arches'
    class Admin:
        pass

class Repo(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(maxlength=255,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'repos'
        ordering = ['name']
        verbose_name_plural = 'repos'
    class Admin:
        pass

class Package(models.Model):
    id = models.AutoField(primary_key=True)
    repo = models.ForeignKey(Repo)
    arch = models.ForeignKey(Arch)
    maintainer = models.ForeignKey(User, related_name='package_maintainer')
    needupdate = models.BooleanField(default=False)
    pkgname = models.CharField(maxlength=255)
    pkgver = models.CharField(maxlength=255)
    pkgrel = models.CharField(maxlength=255)
    pkgdesc = models.CharField(maxlength=255)
    url = models.CharField(maxlength=255)
    last_update = models.DateTimeField(null=True, blank=True)
    objects = PackageManager()
    class Meta:
        db_table = 'packages'
        get_latest_by = 'last_update'

    def __str__(self):
        return self.pkgname

    def get_absolute_url(self):
        return '/packages/%i/' % self.id

    def get_requiredby(self):
        """
        Returns a list of tuples(2). 

        Each tuple in the list is as follows: (packageid, packagename)
        """
        reqs = []
        requiredby = PackageDepend.objects.filter(depname=self.pkgname).filter(
            Q(pkg__arch=self.arch) | Q(pkg__arch__name__iexact='any')
            ).order_by('depname')
        for req in requiredby:
            reqs.append((req.pkg.id,req.pkg.pkgname))
        ## sort the resultant array. Django has problems in the orm with
        ## trying to shoehorn the sorting into the reverse foreign key 
        ## reference in the query above. :(
        reqs.sort(lambda a,b: cmp(a[1],b[1]))
        return reqs

    def get_depends(self):
        """
        Returns a list of tuples(3). 

        Each tuple in the list is one of:
         - (packageid, dependname, depend compare string) if a matching 
           package is found.
         - (None, dependname, None) if no matching package is found, eg 
           it is a virtual dep.
        """
        deps = []
        for dep in self.packagedepend_set.order_by('depname'):
            # we only need depend on same-arch-packages
            pkgs = Package.objects.filter(
                Q(arch__name__iexact='any') | Q(arch=self.arch),
                pkgname=dep.depname)
            if len(pkgs) == 0:
                # couldn't find a package in the DB
                # it should be a virtual depend (or a removed package)
                deps.append((None, dep.depname, None))
                continue
            else:
                for p in pkgs:
                    deps.append((p.id,dep.depname,dep.depvcmp))
        return deps

class PackageFile(models.Model):
    id = models.AutoField(primary_key=True)
    pkg = models.ForeignKey('Package')
    path = models.CharField(maxlength=255)
    class Meta:
        db_table = 'package_files'

class PackageDepend(models.Model):
    id = models.AutoField(primary_key=True)
    pkg = models.ForeignKey('Package')
    depname = models.CharField(db_index=True, maxlength=255)
    depvcmp = models.CharField(maxlength=255)
    class Meta:
        db_table = 'package_depends'

class Todolist(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User, related_name='todolist_creator')
    name = models.CharField(maxlength=255)
    description = models.TextField()
    date_added = models.DateField(auto_now_add=True)
    objects = TodolistManager()
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'todolists'

class TodolistPkg(models.Model):
    id = models.AutoField(primary_key=True)
    list = models.ForeignKey('Todolist')
    pkg = models.ForeignKey('Package')
    complete = models.BooleanField(default=False)
    class Meta:
        db_table = 'todolist_pkgs'
        unique_together = (('list','pkg'),)

class Wikipage(models.Model):
    """Wiki page storage"""
    title = models.CharField(maxlength=255)
    content = models.TextField()
    last_author = models.ForeignKey(User, related_name='wikipage_last_author')
    class Meta:
        db_table = 'wikipages'

    def editurl(self):
        return "/wiki/edit/" + self.title + "/"

    def __str__(self):
        return self.title

# vim: set ts=4 sw=4 et:


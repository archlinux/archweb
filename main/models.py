from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
import re

###########################
### Model help classes  ###
###########################
class Container(dict):
    def __init__(self, dict_entries=None, **entries):
        if dict_entries:
            self.update(dict_entries)
        if entries:
            self.update(entries)

    def __iter__(self):
        rev_items = [(v, k) for k, v in self.items()]
        rev_items.sort()
        items = [k for v, k in rev_items]
        return items.__iter__()

    def itertransp(self):
        rev_items = [(v, k) for k, v in self.items()]
        rev_items.sort()
        return rev_items.__iter__()

    def __getattr__(self,name):
        return self[name]

    def __setattr__(self,name,val):
        self[name] = val

    
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
    user = models.ForeignKey(User, related_name='userprofile_user',  edit_inline=models.STACKED, num_in_admin=1, min_num_in_admin=1, max_num_in_admin=1, num_extra_on_change=0, unique=True)
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
            if TodolistPkg.objects.filter(list=l.id).filter(complete=False).count() > 0:
                results.append(l)
        return results

class PackageManager(models.Manager):
    def get_flag_stats(self):
        results = []
        # first the orphans
        noflag = self.filter(maintainer=0).count()
        flagged = self.filter(maintainer=0).filter(needupdate=True).count()
        flagnotest = self.filter(maintainer=0).filter(
                        needupdate=True).exclude(
                            repo=Package.REPOS['testing']).count()
        results.append(
            (User(id=0,first_name='Orphans'), noflag, flagged, flagnotest))
        # now the rest
        for maint in User.objects.all().order_by('first_name'):
            noflag = self.filter(maintainer=maint.id).count()
            flagged = self.filter(maintainer=maint.id).filter(
                    needupdate=True).count()
            flagnotest = self.filter(maintainer=maint.id).filter(
                    needupdate=True).exclude(
                        repo=Package.REPOS['testing']).count()
            results.append((maint, noflag, flagged, flagnotest))
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
    class Meta:
        db_table = 'news'
        verbose_name_plural = 'news'
        get_latest_by = 'postdate'
        ordering = ['-postdate', '-id']

    def get_absolute_url(self):
        return '/news/%i/' % self.id

class Package(models.Model):
    ## note: purposefully inlining arch and repo.
    ## they don't change very often (rarely), and it should help compact
    ## the general model
    # architectures
    ARCHES = Container(any=1, i686=2, x86_64=3)
    # repositories
    REPOS = Container(core=1, extra=2, testing=3, unstable=4)

    id = models.AutoField(primary_key=True)
    ## note: the arch and repo elements might need to be indexed. not sure.
    repo = models.IntegerField(choices=REPOS.itertransp())
    arch = models.IntegerField(choices=ARCHES.itertransp())
    maintainer = models.ForeignKey(User, related_name='package_maintainer')
    needupdate = models.BooleanField(default=False)
    pkgname = models.CharField(maxlength=255)
    pkgver = models.CharField(maxlength=255)
    pkgrel = models.CharField(maxlength=255)
    pkgdesc = models.CharField(maxlength=255)
    url = models.URLField()
    last_update = models.DateTimeField(null=True, blank=True)
    objects = PackageManager()
    class Meta:
        db_table = 'packages'
        get_latest_by = 'last_update'

    def get_absolute_url(self):
        return '/packages/%i/' % self.id

    def required_by_urlize(self):
        urls = []
        requiredby = PackageDepend.objects.filter(depname=self.pkgname).order_by('depname')
        for req in requiredby:
            urls.append('<li><a href="/packages/%d/">%s</a></li>' % (req.pkg.id,req.pkg.pkgname))
        return ''.join(urls)

    def depends_urlize(self):
        urls = []
        for dep in self.packagedepend_set.order_by('depname'):
            try:
                # we only need depend on same-arch-packages
                p = Package.objects.get(
                    Q(arch=Package.ARCHES['any']) | Q(arch=self.arch),
                    pkgname=dep.depname)
            except Package.DoesNotExist, IndexError:
                # couldn't find a package in the DB
                # it might be a virtual depend
                urls.append('<li>%s</li>' % dep.depname)
                continue
            urls.append(
                '<li><a href="/packages/%d/">%s</a>%s</li>' % \
                (p.id,dep.depname,dep.depvcmp))
        return ''.join(urls)

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

    def __repr__(self):
        return self.title

# vim: set ts=4 sw=4 et:


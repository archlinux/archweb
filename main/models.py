from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from archweb_dev.main.middleware import get_user

###########################
### User Profile Class ####
###########################
class UserProfile(models.Model):
    id = models.AutoField(primary_key=True) # not technically needed
    notify = models.BooleanField(
        "Send notifications",
        default=True,
        help_text="When enabled, send user 'flag out of date' notifications")
    alias = models.CharField(
        max_length=50,
        help_text="Required field")
    public_email = models.CharField(
        max_length=50,
        help_text="Required field")
    other_contact = models.CharField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=200, null=True, blank=True)
    yob = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    languages = models.CharField(max_length=50, null=True, blank=True)
    interests = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    roles = models.CharField(max_length=255, null=True, blank=True)
    favorite_distros = models.CharField(max_length=255, null=True, blank=True)
    picture = models.FileField(upload_to='devs', default='devs/silhouette.png')
    user = models.ForeignKey(
        User, related_name='userprofile_user', unique=True)
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Additional Profile Data'
        verbose_name_plural = 'Additional Profile Data'


#######################
### Manager Classes ###
#######################
class TodolistManager(models.Manager):
    def incomplete(self):
        return self.filter(todolistpkg__complete=False).distinct()

class PackageManager(models.Manager):
    def flagged(self):
        return self.get_query_set().filter(needupdate=True)

#############################
### General Model Classes ###
#############################
class Mirror(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255, db_index=True)
    admin_email = models.EmailField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    public = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    isos = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name

class MirrorProtocol(models.Model):
    protocol = models.CharField(max_length=10, unique=True)
    def __unicode__(self):
        return self.protocol
    class Meta:
        verbose_name = 'Mirror Protocol'

class MirrorUrl(models.Model):
    url = models.CharField(max_length=255)
    protocol = models.ForeignKey(MirrorProtocol, related_name="urls")
    mirror = models.ForeignKey(Mirror, related_name="urls")
    def __unicode__(self):
        return self.url
    class Meta:
        verbose_name = 'Mirror URL'

class MirrorRsync(models.Model):
    hostname = models.CharField(max_length=255)
    ip = models.CharField(max_length=24)
    mirror = models.ForeignKey(Mirror, related_name="rsync_ips")
    def __unicode__(self):
        return "%s (%s)" % (self.ip, self.hostname)
    class Meta:
        verbose_name = 'Mirror Rsync IP'

class Press(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'press'
        verbose_name_plural = 'press'

class AltForum(models.Model):
    id = models.AutoField(primary_key=True)
    language = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'alt_forums'
        verbose_name = 'AltForum'

class Donor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'donors'

class News(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, related_name='news_author',
            default=get_user)
    postdate = models.DateField(auto_now_add=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    def __unicode__(self):
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
    name = models.CharField(max_length=255,unique=True)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'arches'
        ordering = ['name']
        verbose_name_plural = 'arches'

class Repo(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,unique=True)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'repos'
        ordering = ['name']
        verbose_name_plural = 'repos'

class Package(models.Model):
    id = models.AutoField(primary_key=True)
    repo = models.ForeignKey(Repo, related_name="packages")
    arch = models.ForeignKey(Arch, related_name="packages")
    maintainer = models.ForeignKey(User, related_name="maintained_packages")
    needupdate = models.BooleanField(default=False)
    pkgname = models.CharField(max_length=255)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    pkgdesc = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    last_update = models.DateTimeField(null=True, blank=True)
    license = models.CharField(max_length=255)
    objects = PackageManager()
    class Meta:
        db_table = 'packages'
        ordering = ('pkgname',)
        #get_latest_by = 'last_update'
        #ordering = ('-last_update',)

    def __unicode__(self):
        return self.pkgname

    # According to http://code.djangoproject.com/ticket/2583 we have "bad data"
    # The problem is the queries constructed by the admin  to retrieve foreign
    # keys are empty. This allows us to display items in the list but kills
    # sorting
    def _reponame(self):
        return self.repo.name
    _reponame.short_description='Repo'
    def _archname(self):
        return self.arch.name
    _archname.short_description='Arch'
    def _maintainername(self):
        return self.maintainer.username
    _maintainername.short_description = 'Maintainer'

    def get_absolute_url(self):
        return '/packages/%s/%s/%s/' % (self.repo.name.lower(),
                self.arch.name, self.pkgname)

    @property
    def signoffs(self):
        return Signoff.objects.filter(
            pkg=self,
            pkgver=self.pkgver,
            pkgrel=self.pkgrel)

    def approved_for_signoff(self):
        return self.signoffs.count() >= 2


    def get_requiredby(self):
        """
        Returns a list of package objects.
        """
        requiredby = Package.objects.filter(
                packagedepend__depname=self.pkgname,
                arch__name__in=(self.arch.name, 'Any'))
        return requiredby.order_by('pkgname')

    def get_depends(self):
        """
        Returns a list of tuples(3). 

        Each tuple in the list is one of:
         - (packageid, dependname, depend compare string) if a matching 
           package is found.
         - (None, dependname, None) if no matching package is found, eg 
           it is a virtual dep.
        """
        # object level cache. Doesn't last long, but helps for items rendered
        # twice in the same template.
        if 'deps_cache' in dir(self):
            return self.deps_cache
        deps = []
        for dep in self.packagedepend_set.order_by('depname'):
            # we only need depend on same-arch-packages
            pkgs = Package.objects.filter(
                Q(arch__name__iexact='any') | Q(arch=self.arch),
                pkgname=dep.depname)
            if len(pkgs) == 0:
                # couldn't find a package in the DB
                # it should be a virtual depend (or a removed package)
                deps.append({'dep': dep, 'pkg': None})
            elif len(pkgs) == 1:
                deps.append({'dep': dep, 'pkg': pkgs[0]})
            else:
                tpkgs = pkgs.filter(repo__name='Testing')
                if len(tpkgs) == 1:
                    deps.append({'dep': dep, 'pkg': tpkgs[0]})
                else:
                    for pkg in pkgs:
                        deps.append({'dep': dep, 'pkg': pkg})
        self.deps_cache = deps
        return deps

class Signoff(models.Model):
    pkg = models.ForeignKey(Package)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    packager = models.ForeignKey(User)

class PackageFile(models.Model):
    id = models.AutoField(primary_key=True)
    pkg = models.ForeignKey('Package')
    path = models.CharField(max_length=255)
    class Meta:
        db_table = 'package_files'

class PackageDepend(models.Model):
    id = models.AutoField(primary_key=True)
    pkg = models.ForeignKey('Package')
    depname = models.CharField(db_index=True, max_length=255)
    depvcmp = models.CharField(max_length=255)
    class Meta:
        db_table = 'package_depends'

class Todolist(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date_added = models.DateField(auto_now_add=True)
    objects = TodolistManager()
    def __unicode__(self):
        return self.name

    @property
    def packages(self):
        return TodolistPkg.objects.filter(list=self.id).order_by('pkg')

    @property
    def package_names(self):
        return '\n'.join(set([p.pkg.pkgname for p in self.packages]))

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

# vim: set ts=4 sw=4 et:


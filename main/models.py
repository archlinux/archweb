from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from main.utils import cache_function
from packages.models import PackageRelation

from itertools import groupby
from operator import attrgetter

class UserProfile(models.Model):
    notify = models.BooleanField(
        "Send notifications",
        default=True,
        help_text="When enabled, send user 'flag out-of-date' notifications")
    alias = models.CharField(
        max_length=50,
        help_text="Required field")
    public_email = models.CharField(
        max_length=50,
        help_text="Required field")
    other_contact = models.CharField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=200, null=True, blank=True)
    yob = models.IntegerField("Year of birth", null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    languages = models.CharField(max_length=50, null=True, blank=True)
    interests = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    roles = models.CharField(max_length=255, null=True, blank=True)
    favorite_distros = models.CharField(max_length=255, null=True, blank=True)
    picture = models.FileField(upload_to='devs', default='devs/silhouette.png',
        help_text="Ideally 125px by 125px")
    user = models.OneToOneField(User, related_name='userprofile')
    allowed_repos = models.ManyToManyField('Repo', blank=True)
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Additional Profile Data'
        verbose_name_plural = 'Additional Profile Data'


class TodolistManager(models.Manager):
    def incomplete(self):
        return self.filter(todolistpkg__complete=False).distinct()

class PackageManager(models.Manager):
    def flagged(self):
        return self.get_query_set().filter(flag_date__isnull=False)


class Donor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    visible = models.BooleanField(default=True,
            help_text="Should we show this donor on the public page?")

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'donors'
        ordering = ['name']

class Arch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    agnostic = models.BooleanField(default=False,
            help_text="Is this architecture non-platform specific?")

    def __unicode__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    class Meta:
        db_table = 'arches'
        ordering = ['name']
        verbose_name_plural = 'arches'

class Repo(models.Model):
    name = models.CharField(max_length=255, unique=True)
    testing = models.BooleanField(default=False,
            help_text="Is this repo meant for package testing?")
    bugs_project = models.SmallIntegerField(default=1,
            help_text="Flyspray project ID for this repository.")
    svn_root = models.CharField(max_length=64,
            help_text="SVN root (e.g. path) for this repository.")

    def __unicode__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    class Meta:
        db_table = 'repos'
        ordering = ['name']
        verbose_name_plural = 'repos'

class Package(models.Model):
    repo = models.ForeignKey(Repo, related_name="packages")
    arch = models.ForeignKey(Arch, related_name="packages")
    pkgname = models.CharField(max_length=255, db_index=True)
    pkgbase = models.CharField(max_length=255, db_index=True)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    pkgdesc = models.CharField(max_length=255, null=True)
    url = models.CharField(max_length=255, null=True)
    filename = models.CharField(max_length=255)
    # TODO: it would be nice to have the >0 check constraint back here
    compressed_size = models.BigIntegerField(null=True)
    installed_size = models.BigIntegerField(null=True)
    build_date = models.DateTimeField(null=True)
    last_update = models.DateTimeField(null=True, blank=True)
    files_last_update = models.DateTimeField(null=True, blank=True)
    license = models.CharField(max_length=255, null=True)
    packager_str = models.CharField(max_length=255)
    packager = models.ForeignKey(User, null=True)
    flag_date = models.DateTimeField(null=True)

    objects = PackageManager()
    class Meta:
        db_table = 'packages'
        ordering = ('pkgname',)
        #get_latest_by = 'last_update'
        #ordering = ('-last_update',)

    def __unicode__(self):
        return self.pkgname

    def get_absolute_url(self):
        return '/packages/%s/%s/%s/' % (self.repo.name.lower(),
                self.arch.name, self.pkgname)

    def get_full_url(self, proto='http'):
        '''get a URL suitable for things like email including the domain'''
        domain = Site.objects.get_current().domain
        return '%s://%s%s' % (proto, domain, self.get_absolute_url())

    @property
    def maintainers(self):
        return User.objects.filter(
                package_relations__pkgbase=self.pkgbase,
                package_relations__type=PackageRelation.MAINTAINER)

    @property
    def signoffs(self):
        if 'signoffs_cache' in dir(self):
            return self.signoffs_cache
        self.signoffs_cache = list(Signoff.objects.filter(
            pkg=self,
            pkgver=self.pkgver,
            pkgrel=self.pkgrel))
        return self.signoffs_cache

    def approved_for_signoff(self):
        return len(self.signoffs) >= 2

    @cache_function(300)
    def applicable_arches(self):
        '''The list of (this arch) + (available agnostic arches).'''
        arches = set(Arch.objects.filter(agnostic=True))
        arches.add(self.arch)
        return list(arches)

    @cache_function(300)
    def get_requiredby(self):
        """
        Returns a list of package objects. An attempt will be made to keep this
        list slim by including the corresponding package in the same testing
        category as this package if that check makes sense.
        """
        requiredby = Package.objects.select_related('arch', 'repo').filter(
                packagedepend__depname=self.pkgname,
                arch__in=self.applicable_arches()
                ).distinct().order_by('pkgname')

        # find another package by this name in the opposite testing setup
        if not Package.objects.filter(pkgname=self.pkgname,
                arch=self.arch).exclude(id=self.id,
                repo__testing=self.repo.testing).exists():
            # there isn't one? short circuit, all required by entries are fine
            return requiredby

        trimmed = []
        # for each unique package name, try to screen our package list down to
        # those packages in the same testing category (yes or no) iff there is
        # a package in the same testing category.
        for name, pkgs in groupby(requiredby, attrgetter('pkgname')):
            pkgs = list(pkgs)
            pkg = pkgs[0]
            if len(pkgs) > 1:
                pkgs = [p for p in pkgs if p.repo.testing == self.repo.testing]
                if len(pkgs) > 0:
                    pkg = pkgs[0]
            trimmed.append(pkg)
        return trimmed

    @cache_function(300)
    def get_depends(self):
        """
        Returns a list of dicts. Each dict contains ('pkg' and 'dep'). If it
        represents a found package both vars will be available; else pkg will
        be None if it is a 'virtual' dependency. Packages will match the
        testing status of this package if possible.
        """
        deps = []
        # TODO: we can use list comprehension and an 'in' query to make this more effective
        for dep in self.packagedepend_set.order_by('depname'):
            pkgs = Package.objects.select_related('arch', 'repo').filter(
                    pkgname=dep.depname)
            if not self.arch.agnostic:
                # make sure we match architectures if possible
                pkgs = pkgs.filter(arch__in=self.applicable_arches())
            if len(pkgs) == 0:
                # couldn't find a package in the DB
                # it should be a virtual depend (or a removed package)
                pkg = None
            elif len(pkgs) == 1:
                pkg = pkgs[0]
            else:
                # more than one package, see if we can't shrink it down
                # grab the first though in case we fail
                pkg = pkgs[0]
                # prevents yet more DB queries, these lists should be short
                pkgs = [p for p in pkgs if p.repo.testing == self.repo.testing]
                if len(pkgs) > 0:
                    pkg = pkgs[0]
            deps.append({'dep': dep, 'pkg': pkg})
        return deps

    def base_package(self):
        """
        Locate the base package for this package. It may be this very package,
        or if it was built in a way that the base package isn't real, will
        return None.
        """
        try:
            # start by looking for something in this repo
            return Package.objects.get(arch=self.arch,
                    repo=self.repo, pkgname=self.pkgbase)
        except Package.DoesNotExist:
            # this package might be split across repos? just find one
            # that matches the correct [testing] repo flag
            pkglist = Package.objects.filter(arch=self.arch,
                    repo__testing=self.repo.testing, pkgname=self.pkgbase)
            if len(pkglist) > 0:
                return pkglist[0]
            return None

    def split_packages(self):
        """
        Return all packages that were built with this one (e.g. share a pkgbase
        value). The package this method is called on will never be in the list,
        and we will never return a package that does not have the same
        repo.testing flag. For any non-split packages, the return value will be
        an empty list.
        """
        return Package.objects.filter(arch__in=self.applicable_arches,
                repo__testing=self.repo.testing, pkgbase=self.pkgbase).exclude(id=self.id)

    def get_svn_link(self, svnpath):
        linkbase = "http://projects.archlinux.org/svntogit/%s.git/tree/%s/%s/"
        return linkbase % (self.repo.svn_root, self.pkgbase, svnpath)

    def get_arch_svn_link(self):
        repo = self.repo.name.lower()
        return self.get_svn_link("repos/%s-%s" % (repo, self.arch.name))

    def get_trunk_svn_link(self):
        return self.get_svn_link("trunk")

    def get_bugs_link(self):
        return "https://bugs.archlinux.org/?project=%d&string=%s" % \
                (self.repo.bugs_project, self.pkgname)

    def is_same_version(self, other):
        'is this package similar, name and version-wise, to another'
        return self.pkgname == other.pkgname \
                and self.pkgver == other.pkgver \
                and self.pkgrel == other.pkgrel

    def in_testing(self):
        '''attempt to locate this package in a testing repo; if we are in
        a testing repo we will always return None.'''
        if self.repo.testing:
            return None
        try:
            return Package.objects.get(repo__testing=True,
                    pkgname=self.pkgname, arch=self.arch)
        except Package.DoesNotExist:
            return None

    def elsewhere(self):
        '''attempt to locate this package anywhere else, regardless of
        architecture or repository. Excludes this package from the list.'''
        return Package.objects.select_related('arch', 'repo').filter(
                pkgname=self.pkgname).exclude(id=self.id).order_by(
                'arch__name', 'repo__name')

class Signoff(models.Model):
    pkg = models.ForeignKey(Package)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    packager = models.ForeignKey(User)

class PackageFile(models.Model):
    pkg = models.ForeignKey('Package')
    path = models.CharField(max_length=255)
    class Meta:
        db_table = 'package_files'

class PackageDepend(models.Model):
    pkg = models.ForeignKey('Package')
    depname = models.CharField(db_index=True, max_length=255)
    depvcmp = models.CharField(max_length=255)
    class Meta:
        db_table = 'package_depends'

class Todolist(models.Model):
    creator = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date_added = models.DateField(auto_now_add=True)
    objects = TodolistManager()
    def __unicode__(self):
        return self.name

    @property
    def packages(self):
        # select_related() does not use LEFT OUTER JOIN for nullable ForeignKey
        # fields. That is why we need to explicitly list the ones we want.
        return TodolistPkg.objects.select_related(
            'pkg__repo', 'pkg__arch').filter(list=self).order_by('pkg')

    @property
    def package_names(self):
        # depends on packages property returning a queryset
        return self.packages.values_list('pkg__pkgname', flat=True).distinct()

    class Meta:
        db_table = 'todolists'

    def get_absolute_url(self):
        return '/todo/%i/' % self.id

class TodolistPkg(models.Model):
    list = models.ForeignKey('Todolist')
    pkg = models.ForeignKey('Package')
    complete = models.BooleanField(default=False)
    class Meta:
        db_table = 'todolist_pkgs'
        unique_together = (('list','pkg'),)

# connect signals needed to keep cache in line with reality
from main.utils import refresh_package_latest
from django.db.models.signals import post_save
post_save.connect(refresh_package_latest, sender=Package,
        dispatch_uid="main.models")

# vim: set ts=4 sw=4 et:

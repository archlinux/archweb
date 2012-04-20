from base64 import b64decode
from datetime import datetime
from itertools import groupby
from pgpdump import BinaryData

from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from .fields import PositiveBigIntegerField
from .utils import cache_function, set_created_field, utc_now


class TodolistManager(models.Manager):
    def incomplete(self):
        return self.filter(todolistpkg__complete=False).distinct()

class PackageManager(models.Manager):
    def flagged(self):
        """Used by dev dashboard."""
        return self.filter(flag_date__isnull=False)

    def normal(self):
        return self.select_related('arch', 'repo')

class Donor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    visible = models.BooleanField(default=True,
            help_text="Should we show this donor on the public page?")
    created = models.DateTimeField()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'donors'
        ordering = ('name',)
        get_latest_by = 'when'

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
    staging = models.BooleanField(default=False,
            help_text="Is this repo meant for package staging?")
    bugs_project = models.SmallIntegerField(default=1,
            help_text="Flyspray project ID for this repository.")
    bugs_category = models.SmallIntegerField(default=2,
            help_text="Flyspray category ID for this repository.")
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
    repo = models.ForeignKey(Repo, related_name="packages",
            on_delete=models.PROTECT)
    arch = models.ForeignKey(Arch, related_name="packages",
            on_delete=models.PROTECT)
    pkgname = models.CharField(max_length=255)
    pkgbase = models.CharField(max_length=255, db_index=True)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    epoch = models.PositiveIntegerField(default=0)
    pkgdesc = models.TextField(null=True)
    url = models.CharField(max_length=255, null=True)
    filename = models.CharField(max_length=255)
    compressed_size = PositiveBigIntegerField()
    installed_size = PositiveBigIntegerField()
    build_date = models.DateTimeField(null=True)
    last_update = models.DateTimeField()
    files_last_update = models.DateTimeField(null=True, blank=True)
    packager_str = models.CharField(max_length=255)
    packager = models.ForeignKey(User, null=True,
            on_delete=models.SET_NULL)
    pgp_signature = models.TextField(null=True, blank=True)
    flag_date = models.DateTimeField(null=True)

    objects = PackageManager()

    class Meta:
        db_table = 'packages'
        ordering = ('pkgname',)
        get_latest_by = 'last_update'
        unique_together = (('pkgname', 'repo', 'arch'),)

    def __unicode__(self):
        return self.pkgname

    @property
    def full_version(self):
        if self.epoch > 0:
            return u'%d:%s-%s' % (self.epoch, self.pkgver, self.pkgrel)
        return u'%s-%s' % (self.pkgver, self.pkgrel)

    def get_absolute_url(self):
        return '/packages/%s/%s/%s/' % (self.repo.name.lower(),
                self.arch.name, self.pkgname)

    def get_full_url(self, proto='https'):
        '''get a URL suitable for things like email including the domain'''
        domain = Site.objects.get_current().domain
        return '%s://%s%s' % (proto, domain, self.get_absolute_url())

    @property
    @cache_function(15)
    def signature(self):
        try:
            data = b64decode(self.pgp_signature)
        except TypeError:
            return None
        data = BinaryData(data)
        packets = list(data.packets())
        return packets[0]

    @property
    @cache_function(15)
    def signer(self):
        sig = self.signature
        if sig and sig.key_id:
            try:
                user = User.objects.get(
                        userprofile__pgp_key__endswith=sig.key_id)
            except User.DoesNotExist:
                user = None
            return user
        return None

    _maintainers = None

    @property
    def maintainers(self):
        from packages.models import PackageRelation
        if self._maintainers is None:
            self._maintainers = User.objects.filter(
                    package_relations__pkgbase=self.pkgbase,
                    package_relations__type=PackageRelation.MAINTAINER)
        return self._maintainers

    @maintainers.setter
    def maintainers(self, maintainers):
        self._maintainers = maintainers

    @cache_function(1800)
    def applicable_arches(self):
        '''The list of (this arch) + (available agnostic arches).'''
        arches = set(Arch.objects.filter(agnostic=True))
        arches.add(self.arch)
        return list(arches)

    @cache_function(119)
    def get_requiredby(self):
        """
        Returns a list of package objects. An attempt will be made to keep this
        list slim by including the corresponding package in the same testing
        category as this package if that check makes sense.
        """
        provides = set(self.provides.values_list('name', flat=True))
        provides.add(self.pkgname)
        requiredby = PackageDepend.objects.select_related('pkg',
                'pkg__arch', 'pkg__repo').filter(
                depname__in=provides).order_by(
                'pkg__pkgname', 'pkg__arch__name', 'pkg__repo__name')
        if not self.arch.agnostic:
            # make sure we match architectures if possible
            requiredby = requiredby.filter(
                    pkg__arch__in=self.applicable_arches())
        # sort out duplicate packages; this happens if something has a double
        # versioned dep such as a kernel module
        requiredby = [list(vals)[0] for _, vals in
                groupby(requiredby, lambda x: x.pkg.id)]

        # find another package by this name in the opposite testing setup
        # TODO: figure out staging exclusions too
        if not Package.objects.filter(pkgname=self.pkgname,
                arch=self.arch).exclude(id=self.id).exclude(
                repo__testing=self.repo.testing).exists():
            # there isn't one? short circuit, all required by entries are fine
            return requiredby

        trimmed = []
        # for each unique package name, try to screen our package list down to
        # those packages in the same testing category (yes or no) iff there is
        # a package in the same testing category.
        for _, dep_pkgs in groupby(requiredby, lambda x: x.pkg.pkgname):
            dep_pkgs = list(dep_pkgs)
            dep = dep_pkgs[0]
            if len(dep_pkgs) > 1:
                dep_pkgs = [d for d in dep_pkgs
                        if d.pkg.repo.testing == self.repo.testing and
                        d.pkg.repo.staging == self.repo.staging]
                if len(dep_pkgs) > 0:
                    dep = dep_pkgs[0]
            trimmed.append(dep)
        return trimmed

    @cache_function(121)
    def get_depends(self):
        """
        Returns a list of dicts. Each dict contains ('dep', 'pkg', and
        'providers'). If it represents a found package both vars will be
        available; else pkg will be None if it is a 'virtual' dependency.
        If pkg is None and providers are known, they will be available in
        providers.
        Packages will match the testing status of this package if possible.
        """
        deps = []
        arches = None
        if not self.arch.agnostic:
            arches = self.applicable_arches()
        # TODO: we can use list comprehension and an 'in' query to make this more effective
        for dep in self.depends.order_by('optional', 'depname'):
            pkg = dep.get_best_satisfier(arches, testing=self.repo.testing,
                    staging=self.repo.staging)
            providers = None
            if not pkg:
                providers = dep.get_providers(arches,
                        testing=self.repo.testing, staging=self.repo.staging)
            deps.append({'dep': dep, 'pkg': pkg, 'providers': providers})
        return deps

    @cache_function(125)
    def base_package(self):
        """
        Locate the base package for this package. It may be this very package,
        or if it was built in a way that the base package isn't real, will
        return None.
        """
        try:
            # start by looking for something in this repo
            return Package.objects.normal().get(arch=self.arch,
                    repo=self.repo, pkgname=self.pkgbase)
        except Package.DoesNotExist:
            # this package might be split across repos? just find one
            # that matches the correct [testing] repo flag
            pkglist = Package.objects.normal().filter(arch=self.arch,
                    repo__testing=self.repo.testing,
                    repo__staging=self.repo.staging, pkgname=self.pkgbase)
            if len(pkglist) > 0:
                return pkglist[0]
            return None

    def split_packages(self):
        """
        Return all packages that were built with this one (e.g. share a pkgbase
        value). The package this method is called on will never be in the list,
        and we will never return a package that does not have the same
        repo.testing and repo.staging flags. For any non-split packages, the
        return value will be an empty list.
        """
        return Package.objects.normal().filter(arch__in=self.applicable_arches(),
                repo__testing=self.repo.testing, repo__staging=self.repo.staging,
                pkgbase=self.pkgbase).exclude(id=self.id)

    def flag_request(self):
        if not self.flag_date:
            return None
        from packages.models import FlagRequest
        try:
            request = FlagRequest.objects.filter(pkgbase=self.pkgbase,
                    repo=self.repo).latest()
            return request
        except FlagRequest.DoesNotExist:
            return None

    def is_same_version(self, other):
        'is this package similar, name and version-wise, to another'
        return self.pkgname == other.pkgname \
                and self.pkgver == other.pkgver \
                and self.pkgrel == other.pkgrel \
                and self.epoch == other.epoch

    def in_testing(self):
        '''attempt to locate this package in a testing repo; if we are in
        a testing repo we will always return None.'''
        if self.repo.testing:
            return None
        try:
            return Package.objects.normal().get(repo__testing=True,
                    pkgname=self.pkgname, arch=self.arch)
        except Package.DoesNotExist:
            return None

    def in_staging(self):
        '''attempt to locate this package in a staging repo; if we are in
        a staging repo we will always return None.'''
        if self.repo.staging:
            return None
        try:
            return Package.objects.normal().get(repo__staging=True,
                    pkgname=self.pkgname, arch=self.arch)
        except Package.DoesNotExist:
            return None

    def elsewhere(self):
        '''attempt to locate this package anywhere else, regardless of
        architecture or repository. Excludes this package from the list.'''
        return Package.objects.normal().filter(
                pkgname=self.pkgname).exclude(id=self.id).order_by(
                'arch__name', 'repo__name')

class PackageFile(models.Model):
    pkg = models.ForeignKey(Package)
    is_directory = models.BooleanField(default=False)
    directory = models.CharField(max_length=255)
    filename = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return "%s%s" % (self.directory, self.filename or '')

    class Meta:
        db_table = 'package_files'

class PackageDepend(models.Model):
    pkg = models.ForeignKey(Package, related_name='depends')
    depname = models.CharField(max_length=255, db_index=True)
    depvcmp = models.CharField(max_length=255, default='')
    optional = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    def get_best_satisfier(self, arches=None, testing=None, staging=None):
        '''Find a satisfier for this dependency that best matches the given
        criteria. It will not search provisions, but will find packages named
        and matching repo characteristics if possible.'''
        pkgs = Package.objects.normal().filter(pkgname=self.depname)
        if arches is not None:
            # make sure we match architectures if possible
            pkgs = pkgs.filter(arch__in=arches)
        if len(pkgs) == 0:
            # couldn't find a package in the DB
            # it should be a virtual depend (or a removed package)
            return None
        if len(pkgs) == 1:
            return pkgs[0]
        # more than one package, see if we can't shrink it down
        # grab the first though in case we fail
        pkg = pkgs[0]
        # prevents yet more DB queries, these lists should be short;
        # after each grab the best available in case we remove all entries
        if staging is not None:
            pkgs = [p for p in pkgs if p.repo.staging == staging]
        if len(pkgs) > 0:
            pkg = pkgs[0]

        if testing is not None:
            pkgs = [p for p in pkgs if p.repo.testing == testing]
        if len(pkgs) > 0:
            pkg = pkgs[0]

        return pkg

    def get_providers(self, arches=None, testing=None, staging=None):
        '''Return providers of this dep. Does *not* include exact matches as it
        checks the Provision names only, use get_best_satisfier() instead.'''
        pkgs = Package.objects.normal().filter(
                provides__name=self.depname).distinct()
        if arches is not None:
            pkgs = pkgs.filter(arch__in=arches)

        # Logic here is to filter out packages that are in multiple repos if
        # they are not requested. For example, if testing is False, only show a
        # testing package if it doesn't exist in a non-testing repo.
        if staging is not None:
            filtered = {}
            for p in pkgs:
                if p.pkgname not in filtered or p.repo.staging == staging:
                    filtered[p.pkgname] = p
            pkgs = filtered.values()

        if testing is not None:
            filtered = {}
            for p in pkgs:
                if p.pkgname not in filtered or p.repo.testing == testing:
                    filtered[p.pkgname] = p
            pkgs = filtered.values()

        return pkgs

    def __unicode__(self):
        return "%s%s" % (self.depname, self.depvcmp)

    class Meta:
        db_table = 'package_depends'

class Todolist(models.Model):
    creator = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date_added = models.DateTimeField(db_index=True)
    objects = TodolistManager()

    def __unicode__(self):
        return self.name

    _packages = None

    @property
    def packages(self):
        if not self._packages:
            # select_related() does not use LEFT OUTER JOIN for nullable
            # ForeignKey fields. That is why we need to explicitly list the
            # ones we want.
            self._packages = TodolistPkg.objects.select_related(
                'pkg__repo', 'pkg__arch').filter(list=self).order_by('pkg')
        return self._packages

    @property
    def package_names(self):
        # depends on packages property returning a queryset
        return self.packages.values_list('pkg__pkgname', flat=True).distinct()

    class Meta:
        db_table = 'todolists'

    def get_absolute_url(self):
        return '/todo/%i/' % self.id

    def get_full_url(self, proto='https'):
        '''get a URL suitable for things like email including the domain'''
        domain = Site.objects.get_current().domain
        return '%s://%s%s' % (proto, domain, self.get_absolute_url())

class TodolistPkg(models.Model):
    list = models.ForeignKey(Todolist)
    pkg = models.ForeignKey(Package)
    complete = models.BooleanField(default=False)

    class Meta:
        db_table = 'todolist_pkgs'
        unique_together = (('list','pkg'),)

def set_todolist_fields(sender, **kwargs):
    todolist = kwargs['instance']
    if not todolist.date_added:
        todolist.date_added = utc_now()

# connect signals needed to keep cache in line with reality
from main.utils import refresh_latest
from django.db.models.signals import pre_save, post_save

post_save.connect(refresh_latest, sender=Package,
        dispatch_uid="main.models")
pre_save.connect(set_todolist_fields, sender=Todolist,
        dispatch_uid="main.models")
pre_save.connect(set_created_field, sender=Donor,
        dispatch_uid="main.models")

# vim: set ts=4 sw=4 et:

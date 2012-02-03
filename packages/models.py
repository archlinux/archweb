from collections import namedtuple

from django.db import models
from django.db.models.signals import pre_save
from django.contrib.auth.models import User

from main.models import Arch, Repo
from main.utils import set_created_field

class PackageRelation(models.Model):
    '''
    Represents maintainership (or interest) in a package by a given developer.
    It is not a true foreign key to packages as we want to key off
    pkgbase/pkgname instead, as well as preserve this information across
    package deletes, adds, and in all repositories.
    '''
    MAINTAINER = 1
    WATCHER = 2
    TYPE_CHOICES = (
            (MAINTAINER, 'Maintainer'),
            (WATCHER, 'Watcher'),
    )
    pkgbase = models.CharField(max_length=255)
    user = models.ForeignKey(User, related_name="package_relations")
    type = models.PositiveIntegerField(choices=TYPE_CHOICES, default=MAINTAINER)
    created = models.DateTimeField(editable=False)

    def get_associated_packages(self):
        # TODO: delayed import to avoid circular reference
        from main.models import Package
        return Package.objects.normal().filter(pkgbase=self.pkgbase)

    def repositories(self):
        packages = self.get_associated_packages()
        return sorted(set([p.repo for p in packages]))

    def __unicode__(self):
        return u'%s: %s (%s)' % (
                self.pkgbase, self.user, self.get_type_display())

    class Meta:
        unique_together = (('pkgbase', 'user', 'type'),)


class SignoffSpecificationManager(models.Manager):
    def get_from_package(self, pkg):
        '''Utility method to pull all relevant name-version fields from a
        package and get a matching signoff specification.'''
        return self.get(
                pkgbase=pkg.pkgbase, pkgver=pkg.pkgver, pkgrel=pkg.pkgrel,
                epoch=pkg.epoch, arch=pkg.arch, repo=pkg.repo)

    def get_or_default_from_package(self, pkg):
        '''utility method to pull all relevant name-version fields from a
        package and get a matching signoff specification, or return the default
        base case.'''
        try:
            return self.get(
                    pkgbase=pkg.pkgbase, pkgver=pkg.pkgver, pkgrel=pkg.pkgrel,
                    epoch=pkg.epoch, arch=pkg.arch, repo=pkg.repo)
        except SignoffSpecification.DoesNotExist:
            return DEFAULT_SIGNOFF_SPEC

class SignoffSpecification(models.Model):
    '''
    A specification for the signoff policy for this particular revision of a
    package. The default is requiring two signoffs for a given package. These
    are created only if necessary; e.g., if one wanted to override the
    required=2 attribute, otherwise a sane default object is used.
    '''
    pkgbase = models.CharField(max_length=255, db_index=True)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    epoch = models.PositiveIntegerField(default=0)
    arch = models.ForeignKey(Arch)
    repo = models.ForeignKey(Repo)
    user = models.ForeignKey(User, null=True)
    created = models.DateTimeField(editable=False)
    required = models.PositiveIntegerField(default=2,
        help_text="How many signoffs are required for this package?")
    enabled = models.BooleanField(default=True,
        help_text="Is this package eligible for signoffs?")
    known_bad = models.BooleanField(default=False,
        help_text="Is package is known to be broken in some way?")
    comments = models.TextField(null=True, blank=True)

    objects = SignoffSpecificationManager()

    @property
    def full_version(self):
        if self.epoch > 0:
            return u'%d:%s-%s' % (self.epoch, self.pkgver, self.pkgrel)
        return u'%s-%s' % (self.pkgver, self.pkgrel)

    def __unicode__(self):
        return u'%s-%s' % (self.pkgbase, self.full_version)


# fake default signoff spec when we don't have a persisted one in the database
FakeSignoffSpecification = namedtuple('FakeSignoffSpecification',
        ('required', 'enabled', 'known_bad', 'comments'))
DEFAULT_SIGNOFF_SPEC = FakeSignoffSpecification(2, True, False, u'')


class SignoffManager(models.Manager):
    def get_from_package(self, pkg, user, revoked=False):
        '''Utility method to pull all relevant name-version fields from a
        package and get a matching signoff.'''
        not_revoked = not revoked
        return self.get(
                pkgbase=pkg.pkgbase, pkgver=pkg.pkgver, pkgrel=pkg.pkgrel,
                epoch=pkg.epoch, arch=pkg.arch, repo=pkg.repo,
                revoked__isnull=not_revoked, user=user)

    def get_or_create_from_package(self, pkg, user):
        '''Utility method to pull all relevant name-version fields from a
        package and get or create a matching signoff.'''
        return self.get_or_create(
                pkgbase=pkg.pkgbase, pkgver=pkg.pkgver, pkgrel=pkg.pkgrel,
                epoch=pkg.epoch, arch=pkg.arch, repo=pkg.repo,
                revoked=None, user=user)

    def for_package(self, pkg):
        return self.select_related('user').filter(
                pkgbase=pkg.pkgbase, pkgver=pkg.pkgver, pkgrel=pkg.pkgrel,
                epoch=pkg.epoch, arch=pkg.arch, repo=pkg.repo)

class Signoff(models.Model):
    '''
    A signoff for a package (by pkgbase) at a given point in time. These are
    not keyed directly to a Package object so they don't ever get deleted when
    Packages come and go from testing repositories.
    '''
    pkgbase = models.CharField(max_length=255, db_index=True)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    epoch = models.PositiveIntegerField(default=0)
    arch = models.ForeignKey(Arch)
    repo = models.ForeignKey(Repo)
    user = models.ForeignKey(User, related_name="package_signoffs")
    created = models.DateTimeField(editable=False)
    revoked = models.DateTimeField(null=True)
    comments = models.TextField(null=True, blank=True)

    objects = SignoffManager()

    @property
    def packages(self):
        # TODO: delayed import to avoid circular reference
        from main.models import Package
        return Package.objects.normal().filter(pkgbase=self.pkgbase,
                pkgver=self.pkgver, pkgrel=self.pkgrel, epoch=self.epoch,
                arch=self.arch, repo=self.repo)

    @property
    def full_version(self):
        if self.epoch > 0:
            return u'%d:%s-%s' % (self.epoch, self.pkgver, self.pkgrel)
        return u'%s-%s' % (self.pkgver, self.pkgrel)

    def __unicode__(self):
        revoked = u''
        if self.revoked:
            revoked = u' (revoked)'
        return u'%s-%s: %s%s' % (
                self.pkgbase, self.full_version, self.user, revoked)


class FlagRequest(models.Model):
    '''
    A notification the package is out-of-date submitted through the web site.
    '''
    user = models.ForeignKey(User, blank=True, null=True)
    user_email = models.EmailField('email address')
    created = models.DateTimeField(editable=False)
    ip_address = models.IPAddressField('IP address')
    pkgbase = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=255, default='')
    repo = models.ForeignKey(Repo)
    num_packages = models.PositiveIntegerField('number of packages', default=1)
    message = models.TextField('message to developer', blank=True)
    is_spam = models.BooleanField(default=False,
            help_text="Is this comment from a real person?")
    is_legitimate = models.BooleanField(default=True,
            help_text="Is this actually an out-of-date flag request?")

    class Meta:
        get_latest_by = 'created'

    def who(self):
        if self.user:
            return self.user.get_full_name()
        return self.user_email

    def __unicode__(self):
        return u'%s from %s on %s' % (self.pkgbase, self.who(), self.created)

class PackageGroup(models.Model):
    '''
    Represents a group a package is in. There is no actual group entity,
    only names that link to given packages.
    '''
    pkg = models.ForeignKey('main.Package', related_name='groups')
    name = models.CharField(max_length=255, db_index=True)

    def __unicode__(self):
        return "%s: %s" % (self.name, self.pkg)

class License(models.Model):
    pkg = models.ForeignKey('main.Package', related_name='licenses')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Conflict(models.Model):
    pkg = models.ForeignKey('main.Package', related_name='conflicts')
    name = models.CharField(max_length=255, db_index=True)
    comparison = models.CharField(max_length=255, default='')
    version = models.CharField(max_length=255, default='')

    def __unicode__(self):
        if self.version:
            return u'%s%s%s' % (self.name, self.comparison, self.version)
        return self.name

    class Meta:
        ordering = ['name']

class Provision(models.Model):
    pkg = models.ForeignKey('main.Package', related_name='provides')
    name = models.CharField(max_length=255, db_index=True)
    # comparison must be '=' for provides
    comparison = '='
    version = models.CharField(max_length=255, default='')

    def __unicode__(self):
        if self.version:
            return u'%s=%s' % (self.name, self.version)
        return self.name

    class Meta:
        ordering = ['name']

class Replacement(models.Model):
    pkg = models.ForeignKey('main.Package', related_name='replaces')
    name = models.CharField(max_length=255, db_index=True)
    comparison = models.CharField(max_length=255, default='')
    version = models.CharField(max_length=255, default='')

    def __unicode__(self):
        if self.version:
            return u'%s%s%s' % (self.name, self.comparison, self.version)
        return self.name

    class Meta:
        ordering = ['name']


# hook up some signals
for sender in (PackageRelation, SignoffSpecification, Signoff):
    pre_save.connect(set_created_field, sender=sender,
            dispatch_uid="packages.models")

# vim: set ts=4 sw=4 et:

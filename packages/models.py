from collections import namedtuple

from django.db import models
from django.db.models.signals import pre_save
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.models import User

from main.models import Arch, Repo, Package
from main.utils import set_created_field, database_vendor
from packages.alpm import AlpmAPI


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
        return Package.objects.normal().filter(pkgbase=self.pkgbase)

    def repositories(self):
        packages = self.get_associated_packages()
        return sorted({p.repo for p in packages})

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
            return fake_signoff_spec(pkg.arch)


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


# Fake signoff specs for when we don't have persisted ones in the database.
# These have all necessary attributes of the real thing but are lighter weight
# and have no chance of being persisted.
FakeSignoffSpecification = namedtuple('FakeSignoffSpecification',
        ('required', 'enabled', 'known_bad', 'comments'))


def fake_signoff_spec(arch):
    return FakeSignoffSpecification(arch.required_signoffs, True, False, u'')


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
    created = models.DateTimeField(editable=False, db_index=True)
    revoked = models.DateTimeField(null=True)
    comments = models.TextField(null=True, blank=True)

    objects = SignoffManager()

    @property
    def packages(self):
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
    created = models.DateTimeField(editable=False, db_index=True)
    # Great work, Django... https://code.djangoproject.com/ticket/18212
    ip_address = models.GenericIPAddressField(verbose_name='IP address',
            unpack_ipv4=True)
    pkgbase = models.CharField(max_length=255, db_index=True)
    pkgver = models.CharField(max_length=255)
    pkgrel = models.CharField(max_length=255)
    epoch = models.PositiveIntegerField(default=0)
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

    @property
    def full_version(self):
        # Difference here from other implementations at the moment: we need to
        # handle the case of pkgver and pkgrel being null as this table didn't
        # originally have version columns.
        if self.pkgver == '' and self.pkgrel == '':
            return u''
        if self.epoch > 0:
            return u'%d:%s-%s' % (self.epoch, self.pkgver, self.pkgrel)
        return u'%s-%s' % (self.pkgver, self.pkgrel)

    def get_associated_packages(self):
        return Package.objects.normal().filter(
                pkgbase=self.pkgbase,
                repo__testing=self.repo.testing,
                repo__staging=self.repo.staging).order_by(
                'pkgname', 'repo__name', 'arch__name')

    def __unicode__(self):
        return u'%s from %s on %s' % (self.pkgbase, self.who(), self.created)


class UpdateManager(models.Manager):
    def log_update(self, old_pkg, new_pkg):
        '''Utility method to help log an update. This will determine the type
        based on how many packages are passed in, and will pull the relevant
        necesary fields off the given packages.
        Note that in some cases, this is a no-op if we know this database type
        supports triggers to add these rows instead.'''
        if database_vendor(Package, 'write') in ('sqlite', 'postgresql'):
            # we log updates using database triggers for these backends
            return
        update = Update()
        if new_pkg:
            update.action_flag = ADDITION
            update.package = new_pkg
            update.arch = new_pkg.arch
            update.repo = new_pkg.repo
            update.pkgname = new_pkg.pkgname
            update.pkgbase = new_pkg.pkgbase
            update.new_pkgver = new_pkg.pkgver
            update.new_pkgrel = new_pkg.pkgrel
            update.new_epoch = new_pkg.epoch
        if old_pkg:
            if new_pkg:
                update.action_flag = CHANGE
                # ensure we should even be logging this
                if (old_pkg.pkgver == new_pkg.pkgver and
                        old_pkg.pkgrel == new_pkg.pkgrel and
                        old_pkg.epoch == new_pkg.epoch):
                    # all relevant fields were the same; e.g. a force update
                    return
            else:
                update.action_flag = DELETION
                update.arch = old_pkg.arch
                update.repo = old_pkg.repo
                update.pkgname = old_pkg.pkgname
                update.pkgbase = old_pkg.pkgbase

            update.old_pkgver = old_pkg.pkgver
            update.old_pkgrel = old_pkg.pkgrel
            update.old_epoch = old_pkg.epoch

        update.save(force_insert=True)
        return update


class Update(models.Model):
    UPDATE_ACTION_CHOICES = (
        (ADDITION, 'Addition'),
        (CHANGE, 'Change'),
        (DELETION, 'Deletion'),
    )

    package = models.ForeignKey(Package, related_name="updates",
            null=True, on_delete=models.SET_NULL)
    repo = models.ForeignKey(Repo, related_name="updates")
    arch = models.ForeignKey(Arch, related_name="updates")
    pkgname = models.CharField(max_length=255, db_index=True)
    pkgbase = models.CharField(max_length=255)
    action_flag = models.PositiveSmallIntegerField('action flag',
            choices=UPDATE_ACTION_CHOICES)
    created = models.DateTimeField(editable=False, db_index=True)

    old_pkgver = models.CharField(max_length=255, null=True)
    old_pkgrel = models.CharField(max_length=255, null=True)
    old_epoch = models.PositiveIntegerField(null=True)

    new_pkgver = models.CharField(max_length=255, null=True)
    new_pkgrel = models.CharField(max_length=255, null=True)
    new_epoch = models.PositiveIntegerField(null=True)

    objects = UpdateManager()

    class Meta:
        get_latest_by = 'created'

    def is_addition(self):
        return self.action_flag == ADDITION

    def is_change(self):
        return self.action_flag == CHANGE

    def is_deletion(self):
        return self.action_flag == DELETION

    @property
    def old_version(self):
        if self.action_flag == ADDITION:
            return None
        if self.old_epoch > 0:
            return u'%d:%s-%s' % (self.old_epoch, self.old_pkgver, self.old_pkgrel)
        return u'%s-%s' % (self.old_pkgver, self.old_pkgrel)

    @property
    def new_version(self):
        if self.action_flag == DELETION:
            return None
        if self.new_epoch > 0:
            return u'%d:%s-%s' % (self.new_epoch, self.new_pkgver, self.new_pkgrel)
        return u'%s-%s' % (self.new_pkgver, self.new_pkgrel)

    def elsewhere(self):
        return Package.objects.normal().filter(
                pkgname=self.pkgname, arch=self.arch)

    def replacements(self):
        pkgs = Package.objects.normal().filter(
                replaces__name=self.pkgname)
        if not self.arch.agnostic:
            # make sure we match architectures if possible
            arches = set(Arch.objects.filter(agnostic=True))
            arches.add(self.arch)
            pkgs = pkgs.filter(arch__in=arches)
        return pkgs

    def __unicode__(self):
        return u'%s of %s on %s' % (self.get_action_flag_display(),
                self.pkgname, self.created)


class PackageGroup(models.Model):
    '''
    Represents a group a package is in. There is no actual group entity,
    only names that link to given packages.
    '''
    pkg = models.ForeignKey(Package, related_name='groups')
    name = models.CharField(max_length=255, db_index=True)

    def __unicode__(self):
        return "%s: %s" % (self.name, self.pkg)

    class Meta:
        ordering = ('name',)


class License(models.Model):
    pkg = models.ForeignKey(Package, related_name='licenses')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class RelatedToBase(models.Model):
    '''A base class for conflicts/provides/replaces/etc.'''
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=255, default='')

    def get_best_satisfier(self):
        '''Find a satisfier for this related package that best matches the
        given criteria. It will not search provisions, but will find packages
        named and matching repo characteristics if possible.'''
        pkgs = Package.objects.normal().filter(pkgname=self.name)
        if not self.pkg.arch.agnostic:
            # make sure we match architectures if possible
            arches = self.pkg.applicable_arches()
            pkgs = pkgs.filter(arch__in=arches)
        # if we have a comparison operation, make sure the packages we grab
        # actually satisfy the requirements
        if self.comparison and self.version:
            alpm = AlpmAPI()
            pkgs = [pkg for pkg in pkgs if not alpm.available or
                    alpm.compare_versions(pkg.full_version, self.comparison,
                        self.version)]
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
        pkgs = [p for p in pkgs if p.repo.staging == self.pkg.repo.staging]
        if len(pkgs) > 0:
            pkg = pkgs[0]

        pkgs = [p for p in pkgs if p.repo.testing == self.pkg.repo.testing]
        if len(pkgs) > 0:
            pkg = pkgs[0]

        return pkg

    def get_providers(self):
        '''Return providers of this related package. Does *not* include exact
        matches as it checks the Provision names only, use get_best_satisfier()
        instead for exact matches.'''
        pkgs = Package.objects.normal().filter(
                provides__name=self.name).order_by().distinct()
        if not self.pkg.arch.agnostic:
            # make sure we match architectures if possible
            arches = self.pkg.applicable_arches()
            pkgs = pkgs.filter(arch__in=arches)

        # If we have a comparison operation, make sure the packages we grab
        # actually satisfy the requirements.
        alpm = AlpmAPI()
        if alpm.available and self.comparison and self.version:
            pkgs = pkgs.prefetch_related('provides')
            new_pkgs = []
            for package in pkgs:
                for provide in package.provides.all():
                    if provide.name != self.name:
                        continue
                    if alpm.compare_versions(provide.version,
                            self.comparison, self.version):
                        new_pkgs.append(package)
            pkgs = new_pkgs

        # Sort providers by preference. We sort those in same staging/testing
        # combination first, followed by others. We sort by a (staging,
        # testing) match tuple that will be (True, True) in the best case.
        key_func = lambda x: (x.repo.staging == self.pkg.repo.staging,
                x.repo.testing == self.pkg.repo.testing)
        return sorted(pkgs, key=key_func, reverse=True)

    def __unicode__(self):
        if self.version:
            return u'%s%s%s' % (self.name, self.comparison, self.version)
        return self.name

    class Meta:
        abstract = True
        ordering = ('name',)


class Depend(RelatedToBase):
    DEPTYPE_CHOICES = (
        ('D', 'Depend'),
        ('O', 'Optional Depend'),
        ('M', 'Make Depend'),
        ('C', 'Check Depend'),
    )

    pkg = models.ForeignKey(Package, related_name='depends')
    comparison = models.CharField(max_length=255, default='')
    description = models.TextField(null=True, blank=True)
    deptype = models.CharField(max_length=1, default='D',
            choices=DEPTYPE_CHOICES)

    def __unicode__(self):
        '''For depends, we may also have a description and a modifier.'''
        to_str = super(Depend, self).__unicode__()
        if self.description:
            return u'%s: %s' % (to_str, self.description)
        return to_str


class Conflict(RelatedToBase):
    pkg = models.ForeignKey(Package, related_name='conflicts')
    comparison = models.CharField(max_length=255, default='')


class Provision(RelatedToBase):
    pkg = models.ForeignKey(Package, related_name='provides')
    # comparison must be '=' for provides

    @property
    def comparison(self):
        if self.version is not None and self.version != '':
            return '='
        return None


class Replacement(RelatedToBase):
    pkg = models.ForeignKey(Package, related_name='replaces')
    comparison = models.CharField(max_length=255, default='')


# hook up some signals
for sender in (FlagRequest, PackageRelation,
        SignoffSpecification, Signoff, Update):
    pre_save.connect(set_created_field, sender=sender,
            dispatch_uid="packages.models")

# vim: set ts=4 sw=4 et:

from datetime import datetime

from django.db import models
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User

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
        return Package.objects.filter(pkgbase=self.pkgbase).select_related(
                'arch', 'repo')

    def repositories(self):
        packages = self.get_associated_packages()
        return sorted(set([p.repo for p in packages]))

    def __unicode__(self):
        return "%s: %s (%s)" % (
                self.pkgbase, self.user, self.get_type_display())

    class Meta:
        unique_together = (('pkgbase', 'user', 'type'),)

class PackageGroup(models.Model):
    '''
    Represents a group a package is in. There is no actual group entity,
    only names that link to given packages.
    '''
    pkg = models.ForeignKey('main.Package', related_name='groups')
    name = models.CharField(max_length=255)

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


def remove_inactive_maintainers(sender, instance, created, **kwargs):
    # instance is an auth.models.User; we want to remove any existing
    # maintainer relations if the user is no longer active
    if not instance.is_active:
        maint_relations = PackageRelation.objects.filter(user=instance,
                type=PackageRelation.MAINTAINER)
        maint_relations.delete()

def set_created_field(sender, **kwargs):
    # We use this same callback for both Isos and Tests
    obj = kwargs['instance']
    if not obj.created:
        obj.created = datetime.utcnow()

post_save.connect(remove_inactive_maintainers, sender=User,
        dispatch_uid="packages.models")
pre_save.connect(set_created_field, sender=PackageRelation,
        dispatch_uid="packages.models")

# vim: set ts=4 sw=4 et:

from django.db import models
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
        return self.name

class License(models.Model):
    pkg = models.ForeignKey('main.Package', related_name='licenses')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

# vim: set ts=4 sw=4 et:

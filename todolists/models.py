from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_save

from main.models import Arch, Repo, Package
from main.utils import set_created_field


class Todolist(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.PROTECT,
            related_name="created_todolists")
    created = models.DateTimeField(db_index=True)
    last_modified = models.DateTimeField(editable=False)
    raw = models.TextField(blank=True)

    class Meta:
        get_latest_by = 'created'

    def __str__(self):
        return self.name

    @property
    def stripped_description(self):
        return self.description.strip()

    def get_absolute_url(self):
        return '/todo/%s/' % self.slug

    def get_full_url(self, proto='https'):
        '''get a URL suitable for things like email including the domain'''
        domain = Site.objects.get_current().domain
        return '%s://%s%s' % (proto, domain, self.get_absolute_url())

    def packages(self):
        if not hasattr(self, '_packages'):
            self._packages = self.todolistpackage_set.filter(
                    removed__isnull=True).select_related(
                    'pkg', 'repo', 'arch', 'user__userprofile').order_by(
                    'pkgname', 'arch')
        return self._packages


class TodolistPackage(models.Model):
    INCOMPLETE = 0
    COMPLETE = 1
    IN_PROGRESS = 2
    STATUS_CHOICES = (
        (INCOMPLETE, 'Incomplete'),
        (COMPLETE, 'Complete'),
        (IN_PROGRESS, 'In-progress'),
    )

    todolist = models.ForeignKey(Todolist, on_delete=models.CASCADE)
    pkg = models.ForeignKey(Package, null=True, on_delete=models.SET_NULL)
    pkgname = models.CharField(max_length=255)
    pkgbase = models.CharField(max_length=255)
    arch = models.ForeignKey(Arch, on_delete=models.CASCADE)
    repo = models.ForeignKey(Repo, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False)
    last_modified = models.DateTimeField(editable=False)
    removed = models.DateTimeField(null=True, blank=True)
    status = models.SmallIntegerField(default=INCOMPLETE,
            choices=STATUS_CHOICES)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = (('todolist', 'pkgname', 'arch'),)
        get_latest_by = 'created'

    def __str__(self):
        return self.pkgname

    def status_css_class(self):
        return self.get_status_display().lower().replace('-', '')


pre_save.connect(set_created_field, sender=Todolist,
        dispatch_uid="todolists.models")
pre_save.connect(set_created_field, sender=TodolistPackage,
        dispatch_uid="todolists.models")

# vim: set ts=4 sw=4 et:

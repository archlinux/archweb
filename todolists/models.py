from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import pre_save

from main.models import Arch, Package, Repo
from main.utils import set_created_field

from .stages import STAGES


class Todolist(models.Model):
    REBUILD = 0
    TASK = 1

    KIND_CHOICES = (
        (REBUILD, 'Rebuild'),
        (TASK, 'Task'),
    )

    DEFAULT_STAGES = {
        REBUILD: ['draft', 'rebuild_staging', 'test_testing'],
        TASK: ['draft', 'in_progress'],
    }

    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_todolists")
    created = models.DateTimeField(db_index=True)
    kind = models.SmallIntegerField(default=REBUILD, choices=KIND_CHOICES,
                                    help_text='(Rebuild for soname bumps, Task for independent tasks)')
    last_modified = models.DateTimeField(editable=False)
    raw = models.TextField(blank=True)
    stages = models.JSONField(default=list, editable=False)
    # number of stages completed by the todo list as a whole
    progress = models.PositiveSmallIntegerField(default=0, editable=False)

    class Meta:
        get_latest_by = 'created'

    def __str__(self) -> str:
        return self.name

    @property
    def stripped_description(self) -> str:
        return self.description.strip()

    def get_absolute_url(self) -> str:
        return '/todo/%s/' % self.slug

    def get_full_url(self, proto='https') -> str:
        '''get a URL suitable for things like email including the domain'''
        domain = Site.objects.get_current().domain
        return f'{proto}://{domain}{self.get_absolute_url()}'

    def packages(self):
        if not hasattr(self, '_packages'):
            self._packages = self.todolistpackage_set.filter(
                removed__isnull=True).select_related(
                'todolist', 'pkg', 'repo', 'arch', 'user__userprofile').order_by(
                'pkgname', 'arch')
        return self._packages

    @property
    def stage_list(self):
        return [STAGES[key] for key in self.stages]

    @property
    def finished(self) -> bool:
        return self.progress >= len(self.stages)

    @property
    def current_stage(self):
        if self.finished:
            return None
        return self.stage_list[self.progress]

    def per_package_reached(self) -> bool:
        '''Whether a stage asking for per-package completion has been reached.'''
        return any(stage.per_package for stage in self.stage_list[:self.progress + 1])

    def incomplete_packages(self):
        '''Packages that have not completed the current stage.'''
        return self.todolistpackage_set.filter(
            removed__isnull=True, progress__lte=self.progress)

    def can_advance(self) -> bool:
        stage = self.current_stage
        if stage is None:
            return False
        if not stage.per_package:
            return True
        return not self.incomplete_packages().exists()

    def missing_package_names(self):
        '''Names from the raw package list that did not end up in the list,
        e.g. because they are not found in any repository.'''
        present = {tp.pkgname for tp in self.packages()}
        names = dict.fromkeys(s.strip() for s in self.raw.splitlines())
        return [name for name in names if name and name not in present]

    @property
    def kind_str(self):
        '''Todo list kind as str'''
        return self.KIND_CHOICES[self.kind][1]


class TodolistPackage(models.Model):
    todolist = models.ForeignKey(Todolist, on_delete=models.CASCADE)
    pkg = models.ForeignKey(Package, null=True, on_delete=models.SET_NULL)
    pkgname = models.CharField(max_length=255)
    pkgbase = models.CharField(max_length=255)
    arch = models.ForeignKey(Arch, on_delete=models.CASCADE)
    repo = models.ForeignKey(Repo, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False)
    last_modified = models.DateTimeField(editable=False)
    removed = models.DateTimeField(null=True, blank=True)
    # number of todo list stages completed by this package
    progress = models.PositiveSmallIntegerField(default=0)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = (('todolist', 'pkgname', 'arch'),)
        get_latest_by = 'created'

    def __str__(self) -> str:
        return self.pkgname

    @property
    def is_complete(self) -> bool:
        return self.todolist.finished or self.progress > self.todolist.progress

    def status_css_class(self):
        return self.status_str.lower()

    @property
    def status_str(self) -> str:
        return 'Complete' if self.is_complete else 'Incomplete'


pre_save.connect(set_created_field, sender=Todolist, dispatch_uid="todolists.models")
pre_save.connect(set_created_field, sender=TodolistPackage, dispatch_uid="todolists.models")

# vim: set ts=4 sw=4 et:

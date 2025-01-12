from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.template import loader

from main.models import Arch, Package, Repo
from main.utils import set_created_field


class Todolist(models.Model):
    REBUILD = 0
    TASK = 1

    KIND_CHOICES = (
        (REBUILD, 'Rebuild'),
        (TASK, 'Task'),
    )

    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_todolists")
    created = models.DateTimeField(db_index=True)
    kind = models.SmallIntegerField(default=REBUILD, choices=KIND_CHOICES,
                                    help_text='(Rebuild for soname bumps, Task for independent tasks)')
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

    @property
    def kind_str(self):
        '''Todo list kind as str'''
        return self.KIND_CHOICES[self.kind][1]


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
    status = models.SmallIntegerField(default=INCOMPLETE, choices=STATUS_CHOICES)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = (('todolist', 'pkgname', 'arch'),)
        get_latest_by = 'created'

    def __str__(self):
        return self.pkgname

    def status_css_class(self):
        return self.get_status_display().lower().replace('-', '')

    @property
    def status_str(self):
        return self.STATUS_CHOICES[self.status][1]


def check_todolist_complete(sender, instance, **kwargs):
    if instance.status == instance.INCOMPLETE:
        return

    query = TodolistPackage.objects.filter(todolist=instance.todolist, status__exact=instance.INCOMPLETE)
    if query.count() > 0:
        return

    # Send e-mail notification
    subject = "The last package on the TODO list '%s' has been completed." % instance.todolist.name
    tmpl = loader.get_template('todolists/complete_email_notification.txt')
    toemail = [instance.todolist.creator.email]
    ctx = {
        'todolist': instance.todolist,
    }
    msg = EmailMessage(subject, tmpl.render(ctx), 'Arch Website Notification <nobody@archlinux.org>', toemail)
    msg.send(fail_silently=True)


pre_save.connect(set_created_field, sender=Todolist, dispatch_uid="todolists.models")
pre_save.connect(set_created_field, sender=TodolistPackage, dispatch_uid="todolists.models")

post_save.connect(check_todolist_complete, sender=TodolistPackage, dispatch_uid='todolist.models')

# vim: set ts=4 sw=4 et:

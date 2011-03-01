from django.db import models
from django.db.models import Max
from datetime import datetime

# Create your models here.
class Iso(models.Model):
    date = models.DateField()

    def __unicode__(self):
        return str(self.date)

class Architecture(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Isotype(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Boottype(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Hardware(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class InstallType(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Source(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Clockchoice(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Filesystem(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Module(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Bootloader(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
    def get_success_test(self):
        return self.test_set.filter(success=True).aggregate(Max('iso__date'))['iso__date__max']
    def get_failed_test(self):
        return self.test_set.filter(success=False).aggregate(Max('iso__date'))['iso__date__max']

class Test(models.Model):
    user_name = models.CharField(max_length=500)
    user_email = models.EmailField()
    iso = models.ForeignKey(Iso)
    arch = models.ForeignKey(Architecture)
    isotype = models.ForeignKey(Isotype)
    boottype = models.ForeignKey(Boottype)
    hardwaretype = models.ForeignKey(Hardware)
    installtype = models.ForeignKey(InstallType)
    source = models.ForeignKey(Source)
    clock = models.ForeignKey(Clockchoice)
    filesystem = models.ForeignKey(Filesystem)
    ms = models.ManyToManyField(Module, null=True, blank=True)
    rollback = models.BooleanField()
    rollback_filesystem = models.ForeignKey(Filesystem,
            related_name="rollback_test", null=True, blank=True)
    rollback_modules = models.ManyToManyField(Module,
            related_name="rollback_test", null=True, blank=True)
    bootloader = models.ForeignKey(Bootloader)
    success = models.BooleanField()
    comments = models.TextField(null=True, blank=True)

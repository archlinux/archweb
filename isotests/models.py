from datetime import datetime

from django.db import models
from django.db.models import Max

class IsoOption(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=200)

    success_tests = None
    failed_tests = None

    def __unicode__(self):
        return str(self.name)

    def get_success_test(self):
        if not self.success_tests:
            self.success_tests = self.test_set.filter(
                    success=True).annotate(Max('iso__id'))

        if self.success_tests:
            return self.success_tests[0].iso
        return None

    def get_failed_test(self):
        if not self.failed_tests:
            self.failed_tests = self.test_set.filter(
                    success=False).annotate(Max('iso__id'))

        if self.failed_tests:
            return self.failed_tests[0].iso
        return None

class RollbackOption(IsoOption):
    class Meta:
        abstract = True

    success_rollback_tests = None
    failed_rollback_tests = None

    def get_rollback_success_test(self):
        if not self.success_rollback_tests:
            self.success_rollback_tests = self.rollback_test_set.filter(
                    success=True).annotate(Max('iso__id'))

        if self.success_rollback_tests:
            return self.success_rollback_tests[0].iso
        return None

    def get_rollback_failed_test(self):
        if not self.failed_rollback_tests:
            self.failed_rollback_tests = self.rollback_test_set.filter(
                    success=False).annotate(Max('iso__id'))

        if self.failed_rollback_tests:
            return self.failed_rollback_tests[0].iso
        return None

class Iso(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(editable=False)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

class Architecture(IsoOption):
    pass

class IsoType(IsoOption):
    pass

class BootType(IsoOption):
    pass

class HardwareType(IsoOption):
    pass

class InstallType(IsoOption):
    pass

class Source(IsoOption):
    pass

class ClockChoice(IsoOption):
    pass

class Filesystem(RollbackOption):
    pass

class Module(RollbackOption):
    pass

class Bootloader(IsoOption):
    pass

class Test(models.Model):
    user_name = models.CharField(max_length=500)
    user_email = models.EmailField()
    ip_address = models.IPAddressField()
    created = models.DateTimeField(editable=False)

    iso = models.ForeignKey(Iso)
    architecture = models.ForeignKey(Architecture)
    iso_type = models.ForeignKey(IsoType)
    boot_type = models.ForeignKey(BootType)
    hardware_type = models.ForeignKey(HardwareType)
    install_type = models.ForeignKey(InstallType)
    source = models.ForeignKey(Source)
    clock_choice = models.ForeignKey(ClockChoice)
    filesystem = models.ForeignKey(Filesystem)
    modules = models.ManyToManyField(Module, null=True, blank=True)
    rollback_filesystem = models.ForeignKey(Filesystem,
            related_name="rollback_test_set", null=True, blank=True)
    rollback_modules = models.ManyToManyField(Module,
            related_name="rollback_test_set", null=True, blank=True)
    bootloader = models.ForeignKey(Bootloader)

    success = models.BooleanField()
    comments = models.TextField(null=True, blank=True)

def set_created_field(sender, **kwargs):
    # We use this same callback for both Isos and Tests
    obj = kwargs['instance']
    if not obj.created:
        obj.created = datetime.utcnow()

from django.db.models.signals import pre_save

pre_save.connect(set_created_field, sender=Iso,
        dispatch_uid="isotests.models")
pre_save.connect(set_created_field, sender=Test,
        dispatch_uid="isotests.models")

# vim: set ts=4 sw=4 et:

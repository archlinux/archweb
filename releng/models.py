from django.db import models
from django.db.models.signals import pre_save

from main.utils import set_created_field

class IsoOption(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

    def get_test_result(self, success):
        try:
            return self.test_set.filter(success=success).select_related(
                    'iso').latest('iso__id').iso
        except Test.DoesNotExist:
            return None

    def get_last_success(self):
        return self.get_test_result(True)

    def get_last_failure(self):
        return self.get_test_result(False)

    class Meta:
        abstract = True

class RollbackOption(IsoOption):
    def get_rollback_test_result(self, success):
        try:
            return self.rollback_test_set.filter(success=success).select_related(
                    'iso').latest('iso__id').iso
        except Test.DoesNotExist:
            return None

    def get_last_rollback_success(self):
        return self.get_rollback_test_result(True)

    def get_last_rollback_failure(self):
        return self.get_rollback_test_result(False)

    class Meta:
        abstract = True

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
    bootloader = models.ForeignKey(Bootloader)
    rollback_filesystem = models.ForeignKey(Filesystem,
            related_name="rollback_test_set", null=True, blank=True)
    rollback_modules = models.ManyToManyField(Module,
            related_name="rollback_test_set", null=True, blank=True)

    success = models.BooleanField()
    comments = models.TextField(null=True, blank=True)

pre_save.connect(set_created_field, sender=Iso,
        dispatch_uid="releng.models")
pre_save.connect(set_created_field, sender=Test,
        dispatch_uid="releng.models")

# vim: set ts=4 sw=4 et:

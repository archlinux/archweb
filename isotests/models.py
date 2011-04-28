from django.db import models
from django.db.models import Max

class IsoOption(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=200)

    def __unicode__(self):
        return str(self.name)

    def get_success_test(self):
        test = self.test_set.filter(success=True).annotate(Max('iso__id'))
        if test:
            return test[0].iso.name
        return None

    def get_failed_test(self):
        test = self.test_set.filter(success=False).annotate(Max('iso__id'))
        if test:
            return test[0].iso.name
        return None

class Iso(models.Model):
    name = models.CharField(max_length=500)
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

class Filesystem(IsoOption):
    pass

class Module(IsoOption):
    pass

class Bootloader(IsoOption):
    pass

class Test(models.Model):
    user_name = models.CharField(max_length=500)
    user_email = models.EmailField()
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
    rollback = models.BooleanField()
    rollback_filesystem = models.ForeignKey(Filesystem,
            related_name="rollback_test", null=True, blank=True)
    rollback_modules = models.ManyToManyField(Module,
            related_name="rollback_test", null=True, blank=True)
    bootloader = models.ForeignKey(Bootloader)
    success = models.BooleanField()
    comments = models.TextField(null=True, blank=True)

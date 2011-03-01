from django.db import models

# Create your models here.
class Iso(models.Model):
    date = models.DateField()

    def __unicode__(self):
        return str(self.date)

class Hardware(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class InstallType(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class Source(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class Filesystem(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class Module(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class Bootloader(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

class Test(models.Model):
    ARCH_CHOICES = (
        ('d86', 'dual, option i686'),
        ('d64', 'dual, option x86_64'),
        ('x86', 'i686'),
        ('x64', 'x86_64')
    )

    ISOTYPE_CHOICES = (
        ('c', 'core'),
        ('n', 'net')
    )

    BOOTTYPE_CHOICES = (
        ('o', 'optical'),
        ('u', 'usb'),
        ('p', 'pxe')
    )

    CLOCK_CHOICES = (
        ('d', 'default'),
        ('m', 'configured manually'),
        ('n', 'NTP')
    )

    user_name = models.CharField(max_length=500)
    user_email = models.EmailField()
    iso = models.ForeignKey(Iso)
    arch = models.CharField(max_length=3, choices=ARCH_CHOICES)
    isotype = models.CharField(max_length=1, choices=ISOTYPE_CHOICES)
    boottype = models.CharField(max_length=1, choices=BOOTTYPE_CHOICES)
    hardwaretype = models.ForeignKey(Hardware)
    installtype = models.ForeignKey(InstallType)
    source = models.ForeignKey(Source)
    clock = models.CharField(max_length=1, choices=CLOCK_CHOICES)
    filesystem = models.ForeignKey(Filesystem)
    ms = models.ManyToManyField(Module)    
    rollback = models.BooleanField()
    rollback_filesystem = models.ForeignKey(Filesystem, related_name="rollback_test")
    rollback_modules = models.ManyToManyField(Module, related_name="rollback_test")
    success = models.BooleanField()
    comments = models.TextField()

from django.contrib import admin

from .models import (Architecture, BootType, Bootloader, ClockChoice,
        Filesystem, HardwareType, InstallType, Iso, IsoType, Module, Source,
        Test, Release)

class IsoAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'active', 'removed')
    list_filter = ('active', 'created')
    date_hierarchy = 'created'

class TestAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_email', 'created', 'ip_address',
            'iso', 'success')
    list_filter = ('success', 'iso')

class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('version', 'release_date', 'kernel_version', 'available',
            'created')
    list_filter = ('available', 'release_date')


SIMPLE_MODELS = (Architecture, BootType, Bootloader, ClockChoice, Filesystem,
        HardwareType, InstallType, IsoType, Module, Source)

for model in SIMPLE_MODELS:
    admin.site.register(model)

admin.site.register(Iso, IsoAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(Release, ReleaseAdmin)

# vim: set ts=4 sw=4 et:

from django.contrib import admin

from .models import (Architecture, BootType, Bootloader, ClockChoice,
        Filesystem, HardwareType, InstallType, Iso, IsoType, Module, Source,
        Test)

class IsoAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'active', 'removed')
    list_filter = ('active', 'created')
    date_hierarchy = 'created'

class TestAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_email', 'created', 'ip_address',
            'iso', 'success')
    list_filter = ('success', 'iso')


admin.site.register(Architecture)
admin.site.register(BootType)
admin.site.register(Bootloader)
admin.site.register(ClockChoice)
admin.site.register(Filesystem)
admin.site.register(HardwareType)
admin.site.register(InstallType)
admin.site.register(IsoType)
admin.site.register(Module)
admin.site.register(Source)

admin.site.register(Iso, IsoAdmin)
admin.site.register(Test, TestAdmin)

# vim: set ts=4 sw=4 et:

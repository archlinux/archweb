from django.contrib import admin

from .models import (Architecture, BootType, Bootloader, ClockChoice,
        Filesystem, HardwareType, InstallType, Iso, IsoType, Module, Source)

admin.site.register(Iso)
admin.site.register(Architecture)
admin.site.register(IsoType)
admin.site.register(BootType)
admin.site.register(HardwareType)
admin.site.register(InstallType)
admin.site.register(Source)
admin.site.register(ClockChoice)
admin.site.register(Filesystem)
admin.site.register(Module)
admin.site.register(Bootloader)

# vim: set ts=4 sw=4 et:

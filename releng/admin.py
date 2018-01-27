from django.contrib import admin

from .models import (Iso, Release)

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
    readonly_fields = ('created', 'last_modified')


admin.site.register(Iso, IsoAdmin)
admin.site.register(Release, ReleaseAdmin)

# vim: set ts=4 sw=4 et:

from django.contrib import admin

from .models import Release


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('version', 'release_date', 'kernel_version', 'available',
                    'created')
    list_filter = ('available', 'release_date')
    readonly_fields = ('created', 'last_modified')


admin.site.register(Release, ReleaseAdmin)

# vim: set ts=4 sw=4 et:

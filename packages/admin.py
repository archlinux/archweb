from django.contrib import admin

from .models import PackageRelation

class PackageRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'pkgbase', 'type', 'created')
    list_filter = ('type', 'user')
    search_fields = ('user__username', 'pkgbase')

admin.site.register(PackageRelation, PackageRelationAdmin)

# vim: set ts=4 sw=4 et:

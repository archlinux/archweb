from django.contrib import admin

from .models import PackageRelation, FlagRequest

class PackageRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'pkgbase', 'type', 'created')
    list_filter = ('type', 'user')
    search_fields = ('user__username', 'pkgbase')
    date_hierarchy = 'created'

class FlagRequestAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'created', 'who', 'is_spam', 'is_legitimate',
            'message')
    list_filter = ('is_spam', 'is_legitimate')
    search_fields = ('pkgbase', 'user_email', 'message')
    date_hierarchy = 'created'

admin.site.register(PackageRelation, PackageRelationAdmin)
admin.site.register(FlagRequest, FlagRequestAdmin)

# vim: set ts=4 sw=4 et:

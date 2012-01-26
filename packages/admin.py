from django.contrib import admin

from .models import PackageRelation, FlagRequest, Signoff, SignoffSpecification

class PackageRelationAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'user', 'type', 'created')
    list_filter = ('type', 'user')
    search_fields = ('pkgbase', 'user__username')
    ordering = ('pkgbase', 'user')
    date_hierarchy = 'created'

class FlagRequestAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'version', 'repo', 'created', 'who', 'is_spam',
            'is_legitimate', 'message')
    list_filter = ('is_spam', 'is_legitimate', 'repo')
    search_fields = ('pkgbase', 'user_email', 'message')
    ordering = ('-created',)
    date_hierarchy = 'created'


class SignoffAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'full_version', 'arch', 'repo',
            'user', 'created', 'revoked')
    list_filter = ('arch', 'repo', 'user')
    search_fields = ('pkgbase', 'user__username')
    ordering = ('-created',)
    date_hierarchy = 'created'

class SignoffSpecificationAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'full_version', 'arch', 'repo',
            'user', 'created', 'comments')
    list_filter = ('arch', 'repo', 'user')
    search_fields = ('pkgbase', 'user__username')
    ordering = ('-created',)
    date_hierarchy = 'created'


admin.site.register(PackageRelation, PackageRelationAdmin)
admin.site.register(FlagRequest, FlagRequestAdmin)
admin.site.register(Signoff, SignoffAdmin)
admin.site.register(SignoffSpecification, SignoffSpecificationAdmin)

# vim: set ts=4 sw=4 et:

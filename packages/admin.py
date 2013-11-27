from django.contrib import admin

from .models import (PackageRelation, FlagRequest,
        Signoff, SignoffSpecification, Update)


class PackageRelationAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'user', 'type', 'created')
    list_filter = ('type', 'user')
    search_fields = ('pkgbase', 'user__username')
    ordering = ('pkgbase', 'user')
    date_hierarchy = 'created'


class FlagRequestAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'full_version', 'repo', 'created', 'who',
            'is_spam', 'is_legitimate', 'message')
    list_filter = ('is_spam', 'is_legitimate', 'repo', 'created')
    search_fields = ('pkgbase', 'user_email', 'message')
    ordering = ('-created',)

    def get_queryset(self, request):
        qs = super(FlagRequestAdmin, self).queryset(request)
        return qs.select_related('repo', 'user')


class SignoffAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'full_version', 'arch', 'repo',
            'user', 'created', 'revoked')
    list_filter = ('arch', 'repo', 'user', 'created')
    search_fields = ('pkgbase', 'user__username')
    ordering = ('-created',)


class SignoffSpecificationAdmin(admin.ModelAdmin):
    list_display = ('pkgbase', 'full_version', 'arch', 'repo',
            'user', 'created', 'comments')
    list_filter = ('arch', 'repo', 'user', 'created')
    search_fields = ('pkgbase', 'user__username')
    ordering = ('-created',)

    def get_queryset(self, request):
        qs = super(SignoffSpecificationAdmin, self).queryset(request)
        return qs.select_related('arch', 'repo', 'user')


class UpdateAdmin(admin.ModelAdmin):
    list_display = ('pkgname', 'repo', 'arch', 'action_flag',
            'old_version', 'new_version', 'created')
    list_filter = ('action_flag', 'repo', 'arch', 'created')
    search_fields = ('pkgname',)
    ordering = ('-created',)
    raw_id_fields = ('package',)


admin.site.register(PackageRelation, PackageRelationAdmin)
admin.site.register(FlagRequest, FlagRequestAdmin)
admin.site.register(Signoff, SignoffAdmin)
admin.site.register(SignoffSpecification, SignoffSpecificationAdmin)
admin.site.register(Update, UpdateAdmin)

# vim: set ts=4 sw=4 et:

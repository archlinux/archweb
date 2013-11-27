from django.contrib import admin
from main.models import Arch, Donor, Package, Repo


class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'visible', 'created')
    list_filter = ('visible', 'created')
    search_fields = ('name',)
    exclude = ('created',)


class ArchAdmin(admin.ModelAdmin):
    list_display = ('name', 'agnostic', 'required_signoffs')
    list_filter = ('agnostic',)
    search_fields = ('name',)


class RepoAdmin(admin.ModelAdmin):
    list_display = ('name', 'testing', 'staging', 'bugs_project',
            'bugs_category', 'svn_root')
    list_filter = ('testing', 'staging')
    search_fields = ('name',)


class PackageAdmin(admin.ModelAdmin):
    list_display = ('pkgname', 'full_version', 'repo', 'arch', 'packager',
            'last_update', 'build_date')
    list_filter = ('repo', 'arch')
    search_fields = ('pkgname', 'pkgbase', 'pkgdesc')
    date_hierarchy = 'build_date'


admin.site.register(Donor, DonorAdmin)

admin.site.register(Package, PackageAdmin)
admin.site.register(Arch, ArchAdmin)
admin.site.register(Repo, RepoAdmin)

# vim: set ts=4 sw=4 et:

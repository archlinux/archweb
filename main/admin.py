from django.contrib import admin
from archweb_dev.main.models import (AltForum, Arch, Donor, Mirror,
        Package, Press, Repo, UserProfile)
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class AltForumAdmin(admin.ModelAdmin):
    list_display = ('language', 'name')
    list_filter = ('language',)
    ordering = ['name']
    search_fields = ('name',)

class DonorAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ('name',)

class MirrorAdmin(admin.ModelAdmin):
    list_display = ('domain', 'country')
    list_filter = ('country',)
    ordering = ['domain']
    search_fields = ('domain',)

class PackageAdmin(admin.ModelAdmin):
    list_display = ('pkgname', '_reponame', '_archname', '_maintainername')
    list_filter = ('repo', 'arch', 'maintainer')
    ordering = ['pkgname']
    search_fields = ('pkgname',)

class PressAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')
    ordering = ['name']
    search_fields = ('name',)

admin.site.unregister(User)
class UserProfileInline(admin.StackedInline):
    model = UserProfile

class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]


admin.site.register(User, UserProfileAdmin)
admin.site.register(AltForum, AltForumAdmin)
admin.site.register(Donor, DonorAdmin)
admin.site.register(Mirror, MirrorAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(Press, PressAdmin)
admin.site.register(Arch)
admin.site.register(Repo)

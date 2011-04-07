from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from main.models import Arch, Donor, Package, Repo, Todolist, UserProfile

class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'visible')
    list_filter = ('visible',)
    search_fields = ('name',)

class ArchAdmin(admin.ModelAdmin):
    list_display = ('name', 'agnostic')
    list_filter = ('agnostic',)
    search_fields = ('name',)

class RepoAdmin(admin.ModelAdmin):
    list_display = ('name', 'testing', 'staging', 'bugs_project', 'svn_root')
    list_filter = ('testing', 'staging')
    search_fields = ('name',)

class PackageAdmin(admin.ModelAdmin):
    list_display = ('pkgname', 'full_version', 'repo', 'arch', 'packager',
            'last_update', 'build_date')
    list_filter = ('repo', 'arch')
    search_fields = ('pkgname',)

class TodolistAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_added', 'creator', 'description')
    search_fields = ('name', 'description')

admin.site.unregister(User)
class UserProfileInline(admin.StackedInline):
    model = UserProfile

class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


admin.site.register(User, UserProfileAdmin)
admin.site.register(Donor, DonorAdmin)

admin.site.register(Package, PackageAdmin)
admin.site.register(Arch, ArchAdmin)
admin.site.register(Repo, RepoAdmin)

admin.site.register(Todolist, TodolistAdmin)

# vim: set ts=4 sw=4 et:

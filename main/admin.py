from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from archweb_dev.main.models import (AltForum, Arch, Donor,
        Mirror, MirrorProtocol, MirrorUrl, MirrorRsync,
        Package, Press, Repo, UserProfile)

class AltForumAdmin(admin.ModelAdmin):
    list_display = ('language', 'name')
    list_filter = ('language',)
    ordering = ['name']
    search_fields = ('name',)

class DonorAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ('name',)

class MirrorUrlForm(forms.ModelForm):
    class Meta:
        model = MirrorUrl
    def clean_url(self):
        # ensure we always save the URL with a trailing slash
        url = self.cleaned_data["url"].strip()
        if url[-1] == '/':
            return url
        return url + '/'

class MirrorUrlInlineAdmin(admin.TabularInline):
    model = MirrorUrl
    form = MirrorUrlForm
    extra = 3

class MirrorRsyncInlineAdmin(admin.TabularInline):
    model = MirrorRsync
    extra = 2

class MirrorAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'active', 'public', 'isos', 'notes')
    list_filter = ('country', 'active', 'public')
    ordering = ['country', 'name']
    search_fields = ('name',)
    inlines = [
            MirrorUrlInlineAdmin,
            MirrorRsyncInlineAdmin,
    ]

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
admin.site.register(MirrorProtocol)

admin.site.register(Package, PackageAdmin)
admin.site.register(Press, PressAdmin)
admin.site.register(Arch)
admin.site.register(Repo)

# vim: set ts=4 sw=4 et:

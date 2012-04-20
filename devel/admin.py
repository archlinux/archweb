from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, MasterKey, PGPSignature


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


class MasterKeyAdmin(admin.ModelAdmin):
    list_display = ('pgp_key', 'owner', 'created', 'revoker', 'revoked')
    search_fields = ('pgp_key', 'owner', 'revoker')
    date_hierarchy = 'created'


class PGPSignatureAdmin(admin.ModelAdmin):
    list_display = ('signer', 'signee', 'created', 'expires', 'valid')
    list_filter = ('valid',)
    search_fields = ('signer', 'signee')
    date_hierarchy = 'created'


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)

admin.site.register(MasterKey, MasterKeyAdmin)
admin.site.register(PGPSignature, PGPSignatureAdmin)

# vim: set ts=4 sw=4 et:

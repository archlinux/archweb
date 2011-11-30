from django.contrib import admin

from .models import MasterKey


class MasterKeyAdmin(admin.ModelAdmin):
    list_display = ('pgp_key', 'owner', 'created', 'revoker', 'revoked')
    search_fields = ('pgp_key', 'owner', 'revoker')

admin.site.register(MasterKey, MasterKeyAdmin)

# vim: set ts=4 sw=4 et:

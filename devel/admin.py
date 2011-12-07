from django.contrib import admin

from .models import MasterKey, PGPSignature


class MasterKeyAdmin(admin.ModelAdmin):
    list_display = ('pgp_key', 'owner', 'created', 'revoker', 'revoked')
    search_fields = ('pgp_key', 'owner', 'revoker')
    date_hierarchy = 'created'

class PGPSignatureAdmin(admin.ModelAdmin):
    list_display = ('signer', 'signee', 'created', 'expires', 'valid')
    list_filter = ('valid',)
    search_fields = ('signer', 'signee')
    date_hierarchy = 'created'


admin.site.register(MasterKey, MasterKeyAdmin)
admin.site.register(PGPSignature, PGPSignatureAdmin)

# vim: set ts=4 sw=4 et:

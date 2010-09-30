import re

from django import forms
from django.contrib import admin

from .models import Mirror, MirrorProtocol, MirrorUrl, MirrorRsync

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

# ripped off from django.forms.fields, adding netmask ability
ipv4nm_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}(/(\d|[1-2]\d|3[0-2])){0,1}$')
class IPAddressNetmaskField(forms.fields.RegexField):
    default_error_messages = {
        'invalid': u'Enter a valid IPv4 address, possibly including netmask.',
    }

    def __init__(self, *args, **kwargs):
        super(IPAddressNetmaskField, self).__init__(ipv4nm_re, *args, **kwargs)

class MirrorRsyncForm(forms.ModelForm):
    class Meta:
        model = MirrorRsync
    ip = IPAddressNetmaskField(label='IP')

class MirrorRsyncInlineAdmin(admin.TabularInline):
    model = MirrorRsync
    form = MirrorRsyncForm
    extra = 2

class MirrorAdminForm(forms.ModelForm):
    class Meta:
        model = Mirror
    upstream = forms.ModelChoiceField(queryset=Mirror.objects.filter(tier__gte=0, tier__lte=1), required=False)

class MirrorAdmin(admin.ModelAdmin):
    form = MirrorAdminForm
    list_display = ('name', 'tier', 'country', 'active', 'public', 'isos', 'admin_email', 'supported_protocols')
    list_filter = ('tier', 'country', 'active', 'public')
    search_fields = ('name',)
    inlines = [
            MirrorUrlInlineAdmin,
            MirrorRsyncInlineAdmin,
    ]

class MirrorProtocolAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'is_download',)
    list_filter = ('is_download',)

admin.site.register(Mirror, MirrorAdmin)
admin.site.register(MirrorProtocol, MirrorProtocolAdmin)

# vim: set ts=4 sw=4 et:

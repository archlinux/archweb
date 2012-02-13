import re
from urlparse import urlparse, urlunsplit

from django import forms
from django.contrib import admin

from .models import Mirror, MirrorProtocol, MirrorUrl, MirrorRsync

class MirrorUrlForm(forms.ModelForm):
    class Meta:
        model = MirrorUrl
    def clean_url(self):
        # is this a valid-looking URL?
        url_parts = urlparse(self.cleaned_data["url"])
        if not url_parts.scheme:
            raise forms.ValidationError("No URL scheme (protocol) provided.")
        if not url_parts.netloc:
            raise forms.ValidationError("No URL host provided.")
        if url_parts.params or url_parts.query or url_parts.fragment:
            raise forms.ValidationError(
                "URL parameters, query, and fragment elements are not supported.")
        # ensure we always save the URL with a trailing slash
        path = url_parts.path
        if not path.endswith('/'):
            path += '/'
        url = urlunsplit((url_parts.scheme, url_parts.netloc, path, '', ''))
        return url

class MirrorUrlInlineAdmin(admin.TabularInline):
    model = MirrorUrl
    form = MirrorUrlForm
    readonly_fields = ('protocol', 'has_ipv4', 'has_ipv6')
    extra = 3

# ripped off from django.forms.fields, adding netmask ability
IPV4NM_RE = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}(/(\d|[1-2]\d|3[0-2])){0,1}$')

class IPAddressNetmaskField(forms.fields.RegexField):
    default_error_messages = {
        'invalid': u'Enter a valid IPv4 address, possibly including netmask.',
    }

    def __init__(self, *args, **kwargs):
        super(IPAddressNetmaskField, self).__init__(IPV4NM_RE, *args, **kwargs)

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
    upstream = forms.ModelChoiceField(
            queryset=Mirror.objects.filter(tier__gte=0, tier__lte=1),
            required=False)

class MirrorAdmin(admin.ModelAdmin):
    form = MirrorAdminForm
    list_display = ('name', 'tier', 'country', 'active', 'public',
            'isos', 'admin_email')
    list_filter = ('tier', 'active', 'public', 'country') 
    search_fields = ('name',)
    inlines = [
            MirrorUrlInlineAdmin,
            MirrorRsyncInlineAdmin,
    ]

class MirrorProtocolAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'is_download', 'default')
    list_filter = ('is_download', 'default')

admin.site.register(Mirror, MirrorAdmin)
admin.site.register(MirrorProtocol, MirrorProtocolAdmin)

# vim: set ts=4 sw=4 et:

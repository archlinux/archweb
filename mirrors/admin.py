from datetime import datetime
from urllib.parse import urlunsplit, urlparse

from django import forms
from django.contrib import admin

from .models import (Mirror, MirrorProtocol, MirrorUrl, MirrorRsync,
        CheckLocation)


class MirrorUrlForm(forms.ModelForm):
    class Meta:
        model = MirrorUrl
        fields = ('url', 'country', 'bandwidth', 'active')

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


class MirrorRsyncForm(forms.ModelForm):
    class Meta:
        model = MirrorRsync
        fields = ('ip',)


class MirrorRsyncInlineAdmin(admin.TabularInline):
    model = MirrorRsync
    form = MirrorRsyncForm
    extra = 2


class MirrorAdminForm(forms.ModelForm):
    class Meta:
        model = Mirror
        fields = ('name', 'tier', 'upstream', 'admin_email', 'alternate_email',
                'public', 'active', 'isos', 'rsync_user', 'rsync_password',
                'bug', 'notes')

    upstream = forms.ModelChoiceField(
            queryset=Mirror.objects.filter(tier__gte=0, tier__lte=1),
            required=False)


class MirrorAdmin(admin.ModelAdmin):
    form = MirrorAdminForm
    list_display = ('name', 'tier', 'active', 'public',
            'isos', 'admin_email', 'alternate_email')
    list_filter = ('tier', 'active', 'public')
    search_fields = ('name', 'admin_email', 'alternate_email')
    readonly_fields = ('created', 'last_modified')
    inlines = [
            MirrorUrlInlineAdmin,
            MirrorRsyncInlineAdmin,
    ]

    def save_model(self, request, obj, form, change):
        if '~~~' in obj.notes:
            date = datetime.utcnow().strftime('%Y-%m-%d')
            usertext = request.user.get_full_name()
            obj.notes = obj.notes.replace('~~~', '%s (%s)' % (date, usertext))
        obj.save()


class MirrorProtocolAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'is_download', 'default')
    list_filter = ('is_download', 'default')


class CheckLocationAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'source_ip', 'country', 'created')
    search_fields = ('hostname', 'source_ip')


admin.site.register(Mirror, MirrorAdmin)
admin.site.register(MirrorProtocol, MirrorProtocolAdmin)
admin.site.register(CheckLocation, CheckLocationAdmin)

# vim: set ts=4 sw=4 et:

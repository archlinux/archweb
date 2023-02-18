from operator import attrgetter, itemgetter
from urllib.parse import urlparse, urlunsplit
from functools import partial
from datetime import timedelta

from django import forms
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.core.mail import send_mail
from django.template import loader
from django.forms.widgets import (
    Select,
    SelectMultiple,
    CheckboxSelectMultiple,
    TextInput,
    EmailInput
)
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django_countries import countries
from django.contrib.auth.models import Group, User
from captcha.fields import CaptchaField

from ..models import Mirror, MirrorUrl, MirrorProtocol, MirrorRsync, MirrorLog
from ..utils import get_mirror_statuses, get_mirror_errors

import random

# This is populated later, and re-populated every refresh
# This was the only way to get 3 different examples without
# changing the models.py
url_examples = []
TIER_1_MAX_ERROR_RATE = 2
TIER_1_ERROR_TIME_RANGE = 30
TIER_1_MIN_DAYS_AS_TIER_2 = 60

class CaptchaForm(forms.Form):
    captcha = CaptchaField()

    def as_div(self):
        "Returns this form rendered as HTML <divs>s."

        return self._html_output(
            normal_row=u'<div class="captcha">%(label)s <div class="captcha-input">%(field)s%(help_text)s</div></div>',
            error_row=u'%s',
            row_ender='</div>',
            help_text_html=u' <span class="helptext">%s</span>',
            errors_on_separate_row=True)

class MirrorRequestForm(forms.ModelForm):
    upstream = forms.ModelChoiceField(
        queryset=Mirror.objects.filter(
            tier__gte=0,
            tier__lte=1
        ),
        required=False
    )

    class Meta:
        model = Mirror
        fields = ('name', 'tier', 'upstream', 'admin_email', 'alternate_email',
                  'isos', 'active', 'public', 'rsync_user', 'rsync_password', 'notes')

    def __init__(self, *args, **kwargs):
        super(MirrorRequestForm, self).__init__(*args, **kwargs)
        fields = self.fields
        fields['name'].widget.attrs.update({'placeholder': 'Ex: mirror.argentina.co'})
        fields['alternate_email'].widget.attrs.update({'placeholder': 'Optional'})
        fields['rsync_user'].widget.attrs.update({'placeholder': 'Optional'})
        fields['rsync_password'].widget.attrs.update({'placeholder': 'Optional'})
        fields['notes'].widget.attrs.update({'placeholder': 'Optional (Ex: Hosted by ISP GreatISO.bg)'})

    def as_div(self):
        "Returns this form rendered as HTML <divs>s."
        return self._html_output(
            normal_row=u'<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
            error_row=u'%s',
            row_ender='</div>',
            help_text_html=u' <span class="helptext">%s</span>',
            errors_on_separate_row=True)


class MirrorUrlForm(forms.ModelForm):
    class Meta:
        model = MirrorUrl
        fields = ('url', 'country', 'bandwidth', 'active')

    def __init__(self, *args, **kwargs):
        global url_examples

        super(MirrorUrlForm, self).__init__(*args, **kwargs)
        fields = self.fields

        if len(url_examples) == 0:
            url_examples = [
                'Ex: http://mirror.argentina.co/archlinux',
                'Ex: https://mirror.argentina.co/archlinux',
                'Ex: rsync://mirror.argentina.co/archlinux'
            ]

        fields['url'].widget.attrs.update({'placeholder': url_examples.pop()})

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

    def as_div(self):
        "Returns this form rendered as HTML <divs>s."
        return self._html_output(
            normal_row=u'<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
            error_row=u'%s',
            row_ender='</div>',
            help_text_html=u' <span class="helptext">%s</span>',
            errors_on_separate_row=True)


class MirrorRsyncForm(forms.ModelForm):
    class Meta:
        model = MirrorRsync
        fields = ('ip',)

    def __init__(self, *args, **kwargs):
        super(MirrorRsyncForm, self).__init__(*args, **kwargs)
        fields = self.fields
        fields['ip'].widget.attrs.update({'placeholder': 'Ex: 1.2.4.5'})

    def as_div(self):
        "Returns this form rendered as HTML <divs>s."
        return self._html_output(
            normal_row=u'<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
            error_row=u'%s',
            row_ender='</div>',
            help_text_html=u' <span class="helptext">%s</span>',
            errors_on_separate_row=True)


class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False, widget=SelectMultiple(attrs={'size': '12'}))
    protocol = forms.MultipleChoiceField(required=False, widget=CheckboxSelectMultiple)
    ip_version = forms.MultipleChoiceField(
        required=False, label="IP version", choices=(('4', 'IPv4'), ('6', 'IPv6')),
        widget=CheckboxSelectMultiple)
    use_mirror_status = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        fields = self.fields
        fields['country'].choices = [('all', 'All')] + self.get_countries()
        fields['country'].initial = ['all']
        protos = [(p.protocol, p.protocol) for p in MirrorProtocol.objects.filter(is_download=True)]
        initial = MirrorProtocol.objects.filter(is_download=True, default=True)
        fields['protocol'].choices = protos
        fields['protocol'].initial = [p.protocol for p in initial]
        fields['ip_version'].initial = ['4']

    def get_countries(self):
        country_codes = set()
        country_codes.update(MirrorUrl.objects.filter(
            active=True, mirror__active=True).exclude(country='').values_list(
            'country', flat=True).order_by().distinct())
        code_list = [(code, countries.name(code)) for code in country_codes]
        return sorted(code_list, key=itemgetter(1))

    def as_div(self):
        "Returns this form rendered as HTML <divs>s."
        return self._html_output(
            normal_row=u'<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
            error_row=u'%s',
            row_ender='</div>',
            help_text_html=u' <span class="helptext">%s</span>',
            errors_on_separate_row=True)


@csrf_exempt
def generate_mirrorlist(request):
    if request.method == 'POST' or len(request.GET) > 0:
        data = request.POST if request.method == 'POST' else request.GET
        form = MirrorlistForm(data=data)
        if form.is_valid():
            countries = form.cleaned_data['country']
            protocols = form.cleaned_data['protocol']
            use_status = form.cleaned_data['use_mirror_status']
            ipv4 = '4' in form.cleaned_data['ip_version']
            ipv6 = '6' in form.cleaned_data['ip_version']
            return find_mirrors(request, countries, protocols,
                                use_status, ipv4, ipv6)
    else:
        form = MirrorlistForm()

    return render(request, 'mirrors/mirrorlist_generate.html',
                  {'mirrorlist_form': form})


def status_filter(original_urls):
    status_info = get_mirror_statuses()
    scores = {u.id: u.score for u in status_info['urls']}
    urls = []
    for u in original_urls:
        u.score = scores.get(u.id, None)
        # also include mirrors that don't have an up to date score
        # (as opposed to those that have been set with no score)
        if (u.id not in scores) or (u.score and u.score < 100.0):
            urls.append(u)
    # randomize list to prevent users from overloading the first mirror in the returned list
    random.shuffle(urls)
    return urls


def find_mirrors(request, countries=None, protocols=None, use_status=False,
                 ipv4_supported=True, ipv6_supported=True):
    if not protocols:
        protocols = MirrorProtocol.objects.filter(is_download=True)
    elif hasattr(protocols, 'model') and protocols.model == MirrorProtocol:
        # we already have a queryset, no need to query again
        pass
    else:
        protocols = MirrorProtocol.objects.filter(protocol__in=protocols)
    qset = MirrorUrl.objects.select_related().filter(
        protocol__in=protocols, active=True,
        mirror__public=True, mirror__active=True)
    if countries and 'all' not in countries:
        qset = qset.filter(country__in=countries)

    ip_version = Q()
    if ipv4_supported:
        ip_version |= Q(has_ipv4=True)
    if ipv6_supported:
        ip_version |= Q(has_ipv6=True)
    qset = qset.filter(ip_version)

    if not use_status:
        sort_key = attrgetter('country.name', 'mirror.name', 'url')
        urls = sorted(qset, key=sort_key)
        template = 'mirrors/mirrorlist.txt'
    else:
        urls = status_filter(qset)
        template = 'mirrors/mirrorlist_status.txt'

    context = {
        'mirror_urls': urls,
    }
    return render(request, template, context, content_type='text/plain')


def find_mirrors_simple(request, protocol):
    if protocol == 'smart':
        return redirect('mirrorlist_simple', 'http', permanent=True)
    proto = get_object_or_404(MirrorProtocol, protocol=protocol)
    return find_mirrors(request, protocols=[proto])


def mail_mirror_admins(data):
    template = loader.get_template('mirrors/new_mirror_mail_template.txt')

    mirror_maintainer_group = Group.objects.filter(name='Mirror Maintainers')
    mirror_maintainers = User.objects.filter(is_active=True).filter(groups__in=mirror_maintainer_group)

    for maintainer in mirror_maintainers:
        send_mail('A mirror entry was submitted: \'%s\'' % data.get('name'),
                      template.render(data),
                      'Arch Mirror Notification <mirrors@archlinux.org>',
                      [maintainer.email],
                      fail_silently=True)

def validate_tier_1_request(data):
    if data.get('tier') != '1':
        return None

    # If there is no Tier 2 with the same name,
    # We invalidate this Tier 1.
    if not len((tier_2_mirror := Mirror.objects.filter(name=data.get('name'), tier=2, active=True, public=True))):
        return False

    if tier_2_mirror[0].created - now() < timedelta(days=TIER_1_MIN_DAYS_AS_TIER_2):
        return False

    main_url = MirrorUrl.objects.filter(
        url__startswith=data.get('url1-url'),
        mirror=tier_2_mirror[0]
    )

    # If the Tier 2 and Tier 1 does not have matching URL,
    # it requires manual intervention as it's not a direct upgrade.
    if len(main_url) <= 0:
        return False

    # DEBUG entry:
    MirrorLog.objects.create(
        url=main_url[0],
        location=None, 
        check_time=now(), 
        last_sync=None, 
        duration=0.2, is_success=False, error="Test - 404"
    )
    # /DEBUG enry

    error_logs = get_mirror_errors(mirror_id=tier_2_mirror[0].id, cutoff=timedelta(days=TIER_1_ERROR_TIME_RANGE),
                                   show_all=True)

    if error_logs:
        num_o_errors = 0
        for error in error_logs:
            num_o_errors += error['error_count']

            if num_o_errors >= TIER_1_MAX_ERROR_RATE:
                return False

    # Final check, is the mirror old enough to qualify for Tier 1?
    print(tier_2_mirror[0].created)

    return found_mirror

def submit_mirror(request):

    if request.method == 'POST' or len(request.GET) > 0:
        data = request.POST if request.method == 'POST' else request.GET

        captcha_form = CaptchaForm(data=data)

        # data is immutable, need to be copied and modified to enforce
        # active and public is False.
        tmp = data.copy()
        tmp['active'] = False
        tmp['public'] = False
        data = tmp

        mirror_form = MirrorRequestForm(data=data)

        mirror_url1_form = MirrorUrlForm(data=data, prefix="url1")
        if data.get('url2-url') != '':
            mirror_url2_form = MirrorUrlForm(data=data, prefix="url2")
        else:
            mirror_url2_form = MirrorUrlForm(prefix="url2")
        if data.get('url3-url') != '':
            mirror_url3_form = MirrorUrlForm(data=data, prefix="url3")
        else:
            mirror_url3_form = MirrorUrlForm(prefix="url3")
        
        rsync_form = MirrorRsyncForm(data=data)

        mirror_url2_form.fields['url'].required = False
        mirror_url3_form.fields['url'].required = False
        rsync_form.fields['ip'].required = False

        if data.get('tier') == '1':
            if existing_mirror := validate_tier_1_request(data):
                existing_mirror.update(tier=1)
            else:
                return render(
                    request,
                    'mirrors/mirror_submit_error_upgrading.html',
                    {
                        'TIER_1_ERROR_TIME_RANGE': TIER_1_ERROR_TIME_RANGE,
                        'TIER_1_MAX_ERROR_RATE': TIER_1_MAX_ERROR_RATE,
                    }
                )
        else:
            if captcha_form.is_valid() and mirror_form.is_valid() and mirror_url1_form.is_valid():
                try:
                    with transaction.atomic():
                        transaction.on_commit(partial(mail_mirror_admins, data))

                        mirror = mirror_form.save()
                        mirror_url1 = mirror_url1_form.save(commit=False)
                        mirror_url1.mirror = mirror
                        mirror_url1.save()

                        if data.get('url2-url') != '' and mirror_url2_form.is_valid():
                            mirror_url2 = mirror_url2_form.save(commit=False)
                            mirror_url2.mirror = mirror
                            mirror_url2.save()
                        if data.get('url3-url') != '' and mirror_url3_form.is_valid():
                            mirror_url3 = mirror_url3_form.save(commit=False)
                            mirror_url3.mirror = mirror
                            mirror_url3.save()

                        if data.get('ip') != '' and rsync_form.is_valid():
                            rsync = rsync_form.save(commit=False)
                            rsync.mirror = mirror
                            rsync.save()

                except DatabaseError as error:
                    print(error)

    else:
        captcha_form = CaptchaForm()
        mirror_form = MirrorRequestForm()
        mirror_url1_form = MirrorUrlForm(prefix="url1")
        mirror_url2_form = MirrorUrlForm(prefix="url2")
        mirror_url3_form = MirrorUrlForm(prefix="url3")
        rsync_form = MirrorRsyncForm()

        mirror_form.fields['active'].widget = forms.HiddenInput()
        mirror_form.fields['public'].widget = forms.HiddenInput()
        mirror_url2_form.fields['url'].required = False
        mirror_url3_form.fields['url'].required = False
        rsync_form.fields['ip'].required = False

    return render(
        request,
        'mirrors/mirror_submit.html',
        {
            'captcha' : captcha_form,
            'mirror_form': mirror_form,
            'mirror_url1_form': mirror_url1_form,
            'mirror_url2_form': mirror_url2_form,
            'mirror_url3_form': mirror_url3_form,
            'rsync_form': rsync_form
        }
    )

# vim: set ts=4 sw=4 et:

from operator import attrgetter, itemgetter

from django import forms
from django.db.models import Q
from django.forms.widgets import SelectMultiple, CheckboxSelectMultiple
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django_countries import countries

from ..models import MirrorUrl, MirrorProtocol
from ..utils import get_mirror_statuses

import random

class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False,
            widget=SelectMultiple(attrs={'size': '12'}))
    protocol = forms.MultipleChoiceField(required=False,
            widget=CheckboxSelectMultiple)
    ip_version = forms.MultipleChoiceField(required=False,
            label="IP version", choices=(('4','IPv4'), ('6','IPv6')),
            widget=CheckboxSelectMultiple)
    use_mirror_status = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        fields = self.fields
        fields['country'].choices = [('all','All')] + self.get_countries()
        fields['country'].initial = ['all']
        protos = [(p.protocol, p.protocol) for p in
                MirrorProtocol.objects.filter(is_download=True)]
        initial = MirrorProtocol.objects.filter(is_download=True, default=True)
        fields['protocol'].choices = protos
        fields['protocol'].initial = [p.protocol for p in initial]
        fields['ip_version'].initial = ['4']

    def get_countries(self):
        country_codes = set()
        country_codes.update(MirrorUrl.objects.filter(active=True,
                mirror__active=True).exclude(country='').values_list(
                'country', flat=True).order_by().distinct())
        code_list = [(code, countries.name(code)) for code in country_codes]
        return sorted(code_list, key=itemgetter(1))

    def as_div(self):
        "Returns this form rendered as HTML <divs>s."
        return self._html_output(
            normal_row = u'<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
            error_row = u'%s',
            row_ender = '</div>',
            help_text_html = u' <span class="helptext">%s</span>',
            errors_on_separate_row = True)


@csrf_exempt
def generate_mirrorlist(request):
    if request.method == 'POST' or len(request.GET) > 0:
        form = MirrorlistForm(data=request.POST)
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

# vim: set ts=4 sw=4 et:

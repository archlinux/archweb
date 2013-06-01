from datetime import timedelta
from itertools import groupby
import json
from operator import attrgetter, itemgetter

from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django_countries.countries import COUNTRIES

from .models import (Mirror, MirrorUrl, MirrorProtocol, MirrorLog,
        CheckLocation)
from .utils import get_mirror_statuses, get_mirror_errors, DEFAULT_CUTOFF


class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)
    protocol = forms.MultipleChoiceField(required=False,
            widget=CheckboxSelectMultiple)
    ip_version = forms.MultipleChoiceField(required=False,
            label="IP version", choices=(('4','IPv4'), ('6','IPv6')),
            widget=CheckboxSelectMultiple)
    use_mirror_status = forms.BooleanField(required=False)

    countries = dict(COUNTRIES)

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
        countries = [(code, self.countries[code]) for code in country_codes]
        return sorted(countries, key=itemgetter(1))

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
        form = MirrorlistForm(data=request.REQUEST)
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
    # if a url doesn't have a score, treat it as the highest possible
    return sorted(urls, key=lambda x: x.score or 100.0)


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


def mirrors(request):
    mirror_list = Mirror.objects.select_related().order_by('tier', 'name')
    protos = MirrorUrl.objects.values_list(
            'mirror_id', 'protocol__protocol').order_by(
            'mirror__id', 'protocol__protocol').distinct()
    if not request.user.is_authenticated():
        mirror_list = mirror_list.filter(public=True, active=True)
        protos = protos.filter(mirror__public=True, mirror__active=True)
    protos = {k: list(v) for k, v in groupby(protos, key=itemgetter(0))}
    for mirror in mirror_list:
        items = protos.get(mirror.id, [])
        mirror.protocols = [item[1] for item in items]
    return render(request, 'mirrors/mirrors.html',
            {'mirror_list': mirror_list})


def mirror_details(request, name):
    mirror = get_object_or_404(Mirror, name=name)
    if not request.user.is_authenticated() and \
            (not mirror.public or not mirror.active):
        raise Http404
    error_cutoff = timedelta(days=7)

    status_info = get_mirror_statuses(mirror_id=mirror.id)
    checked_urls = {url for url in status_info['urls'] \
            if url.mirror_id == mirror.id}
    all_urls = set(mirror.urls.filter(active=True).select_related('protocol'))
    # Add dummy data for URLs that we haven't checked recently
    other_urls = all_urls.difference(checked_urls)
    for url in other_urls:
        for attr in ('last_sync', 'completion_pct', 'delay', 'duration_avg',
                'duration_stddev', 'score'):
            setattr(url, attr, None)
    all_urls = sorted(checked_urls.union(other_urls), key=attrgetter('url'))

    error_logs = get_mirror_errors(mirror_id=mirror.id, cutoff=error_cutoff)

    context = {
        'mirror': mirror,
        'urls': all_urls,
        'cutoff': error_cutoff,
        'error_logs': error_logs,
    }
    return render(request, 'mirrors/mirror_details.html', context)

def mirror_details_json(request, name):
    mirror = get_object_or_404(Mirror, name=name)
    status_info = get_mirror_statuses(mirror_id=mirror.id)
    data = status_info.copy()
    data['version'] = 3
    to_json = json.dumps(data, ensure_ascii=False,
            cls=ExtendedMirrorStatusJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response


def status(request, tier=None):
    if tier is not None:
        tier = int(tier)
        if tier not in [t[0] for t in Mirror.TIER_CHOICES]:
            raise Http404
    bad_timedelta = timedelta(days=3)
    status_info = get_mirror_statuses()

    urls = status_info['urls']
    good_urls = []
    bad_urls = []
    for url in urls:
        # screen by tier if we were asked to
        if tier is not None and url.mirror.tier != tier:
            continue
        # split them into good and bad lists based on delay
        if not url.delay or url.delay > bad_timedelta:
            bad_urls.append(url)
        else:
            good_urls.append(url)

    error_logs = get_mirror_errors()
    if tier is not None:
        error_logs = [log for log in error_logs
                if log['url__mirror__tier'] == tier]

    context = status_info.copy()
    context.update({
        'good_urls': sorted(good_urls, key=attrgetter('score')),
        'bad_urls': sorted(bad_urls, key=lambda u: u.delay or timedelta.max),
        'error_logs': error_logs,
        'tier': tier,
    })
    return render(request, 'mirrors/status.html', context)


class MirrorStatusJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle datetime.timedelta and MirrorUrl
    serialization. The base class takes care of datetime.datetime types.'''
    url_attributes = ('url', 'protocol', 'last_sync', 'completion_pct',
            'delay', 'duration_avg', 'duration_stddev', 'score')

    def default(self, obj):
        if isinstance(obj, timedelta):
            # always returned as integer seconds
            return obj.days * 24 * 3600 + obj.seconds
        if hasattr(obj, '__iter__'):
            # mainly for queryset serialization
            return list(obj)
        if isinstance(obj, MirrorUrl):
            data = {attr: getattr(obj, attr) for attr in self.url_attributes}
            country = obj.country
            data['country'] = unicode(country.name)
            data['country_code'] = country.code
            return data
        if isinstance(obj, MirrorProtocol):
            return unicode(obj)
        return super(MirrorStatusJSONEncoder, self).default(obj)


class ExtendedMirrorStatusJSONEncoder(MirrorStatusJSONEncoder):
    '''Adds URL check history information.'''
    log_attributes = ('check_time', 'last_sync', 'duration', 'is_success',
            'location_id')

    def default(self, obj):
        if isinstance(obj, MirrorUrl):
            data = super(ExtendedMirrorStatusJSONEncoder, self).default(obj)
            cutoff = now() - DEFAULT_CUTOFF
            data['logs'] = obj.logs.filter(
                    check_time__gte=cutoff).order_by('check_time')
            return data
        if isinstance(obj, MirrorLog):
            return {attr: getattr(obj, attr) for attr in self.log_attributes}
        return super(ExtendedMirrorStatusJSONEncoder, self).default(obj)


def status_json(request, tier=None):
    if tier is not None:
        tier = int(tier)
        if tier not in [t[0] for t in Mirror.TIER_CHOICES]:
            raise Http404
    status_info = get_mirror_statuses()
    data = status_info.copy()
    if tier is not None:
        data['urls'] = [url for url in data['urls'] if url.mirror.tier == tier]
    data['version'] = 3
    to_json = json.dumps(data, ensure_ascii=False, cls=MirrorStatusJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response


class LocationJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle CheckLocation objects.'''

    def default(self, obj):
        if hasattr(obj, '__iter__'):
            # mainly for queryset serialization
            return list(obj)
        if isinstance(obj, CheckLocation):
            return {
                'id': obj.pk,
                'hostname': obj.hostname,
                'source_ip': obj.source_ip,
                'country': unicode(obj.country.name),
                'country_code': obj.country.code,
                'ip_version': obj.ip_version,
            }
        return super(LocationJSONEncoder, self).default(obj)


def locations_json(request):
    data = {}
    data['version'] = 1
    data['locations'] = CheckLocation.objects.all().order_by('pk')
    to_json = json.dumps(data, ensure_ascii=False, cls=LocationJSONEncoder)
    response = HttpResponse(to_json, content_type='application/json')
    return response

# vim: set ts=4 sw=4 et:

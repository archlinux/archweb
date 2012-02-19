from datetime import timedelta
from itertools import groupby
from operator import attrgetter, itemgetter

from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template
from django.utils import simplejson
from django_countries.countries import COUNTRIES

from .models import Mirror, MirrorUrl, MirrorProtocol
from .utils import get_mirror_statuses, get_mirror_errors

COUNTRY_LOOKUP = dict(COUNTRIES)


class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)
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
        country_codes.update(Mirror.objects.filter(active=True).exclude(
                country='').values_list(
                'country', flat=True).order_by().distinct())
        country_codes.update(MirrorUrl.objects.filter(
                mirror__active=True).exclude(country='').values_list(
                'country', flat=True).order_by().distinct())
        countries = [(code, COUNTRY_LOOKUP[code]) for code in country_codes]
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

    return direct_to_template(request, 'mirrors/mirrorlist_generate.html',
            {'mirrorlist_form': form})


def default_protocol_filter(original_urls):
    key_func = attrgetter('real_country')
    sorted_urls = sorted(original_urls, key=key_func)
    urls = []
    for _, group in groupby(sorted_urls, key=key_func):
        cntry_urls = list(group)
        if any(url.protocol.default for url in cntry_urls):
            cntry_urls = [url for url in cntry_urls if url.protocol.default]
        urls.extend(cntry_urls)
    return urls


def status_filter(original_urls):
    status_info = get_mirror_statuses()
    scores = dict((u.id, u.score) for u in status_info['urls'])
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
        ipv4_supported=True, ipv6_supported=True, smart_protocol=False):
    if not protocols:
        protocols = MirrorProtocol.objects.filter(is_download=True)
    elif hasattr(protocols, 'model') and protocols.model == MirrorProtocol:
        # we already have a queryset, no need to query again
        pass
    else:
        protocols = MirrorProtocol.objects.filter(protocol__in=protocols)
    qset = MirrorUrl.objects.select_related().filter(
            protocol__in=protocols,
            mirror__public=True, mirror__active=True)
    if countries and 'all' not in countries:
        qset = qset.filter(Q(country__in=countries) |
                Q(mirror__country__in=countries))

    ip_version = Q()
    if ipv4_supported:
        ip_version |= Q(has_ipv4=True)
    if ipv6_supported:
        ip_version |= Q(has_ipv6=True)
    qset = qset.filter(ip_version)

    if smart_protocol:
        urls = default_protocol_filter(qset)
    else:
        urls = qset

    if not use_status:
        sort_key = attrgetter('real_country', 'mirror.name', 'url')
        urls = sorted(urls, key=sort_key)
        template = 'mirrors/mirrorlist.txt'
    else:
        urls = status_filter(urls)
        template = 'mirrors/mirrorlist_status.txt'

    return direct_to_template(request, template, {
                'mirror_urls': urls,
            },
            mimetype='text/plain')


def find_mirrors_simple(request, protocol):
    if protocol == 'smart':
        # generate a 'smart' mirrorlist, one that only includes FTP mirrors if
        # no HTTP mirror is available in that country.
        return find_mirrors(request, smart_protocol=True)
    proto = get_object_or_404(MirrorProtocol, protocol=protocol)
    return find_mirrors(request, protocols=[proto])


def mirrors(request):
    mirror_list = Mirror.objects.select_related().order_by('tier', 'country')
    if not request.user.is_authenticated():
        mirror_list = mirror_list.filter(public=True, active=True)
    return direct_to_template(request, 'mirrors/mirrors.html',
            {'mirror_list': mirror_list})


def mirror_details(request, name):
    mirror = get_object_or_404(Mirror, name=name)
    if not request.user.is_authenticated() and \
            (not mirror.public or not mirror.active):
        raise Http404

    status_info = get_mirror_statuses()
    checked_urls = [url for url in status_info['urls'] \
            if url.mirror_id == mirror.id]
    all_urls = mirror.urls.select_related('protocol')
    # get each item from checked_urls and supplement with anything in all_urls
    # if it wasn't there
    all_urls = set(checked_urls).union(all_urls)
    all_urls = sorted(all_urls, key=attrgetter('url'))

    return direct_to_template(request, 'mirrors/mirror_details.html',
            {'mirror': mirror, 'urls': all_urls})


def status(request):
    bad_timedelta = timedelta(days=3)
    status_info = get_mirror_statuses()

    urls = status_info['urls']
    good_urls = []
    bad_urls = []
    for url in urls:
        # split them into good and bad lists based on delay
        if not url.delay or url.delay > bad_timedelta:
            bad_urls.append(url)
        else:
            good_urls.append(url)

    context = status_info.copy()
    context.update({
        'good_urls': sorted(good_urls, key=attrgetter('score')),
        'bad_urls': sorted(bad_urls, key=lambda u: u.delay or timedelta.max),
        'error_logs': get_mirror_errors(),
    })
    return direct_to_template(request, 'mirrors/status.html', context)


class MirrorStatusJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle datetime.timedelta and MirrorUrl
    serialization. The base class takes care of datetime.datetime types.'''
    url_attributes = ['url', 'protocol', 'last_sync', 'completion_pct',
            'delay', 'duration_avg', 'duration_stddev', 'score']

    def default(self, obj):
        if isinstance(obj, timedelta):
            # always returned as integer seconds
            return obj.days * 24 * 3600 + obj.seconds
        if hasattr(obj, '__iter__'):
            # mainly for queryset serialization
            return list(obj)
        if isinstance(obj, MirrorUrl):
            data = dict((attr, getattr(obj, attr))
                    for attr in self.url_attributes)
            # get any override on the country attribute first
            country = obj.real_country
            data['country'] = unicode(country.name)
            data['country_code'] = country.code
            return data
        if isinstance(obj, MirrorProtocol):
            return unicode(obj)
        return super(MirrorStatusJSONEncoder, self).default(obj)


def status_json(request):
    status_info = get_mirror_statuses()
    data = status_info.copy()
    data['version'] = 3
    to_json = simplejson.dumps(data, ensure_ascii=False,
            cls=MirrorStatusJSONEncoder)
    response = HttpResponse(to_json, mimetype='application/json')
    return response

# vim: set ts=4 sw=4 et:

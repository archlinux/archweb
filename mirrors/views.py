from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template
from django.utils import simplejson

from main.utils import make_choice
from .models import Mirror, MirrorUrl, MirrorProtocol
from .utils import get_mirror_statuses, get_mirror_errors

import datetime

class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)
    protocol = forms.MultipleChoiceField(required=False)
    ip_version = forms.MultipleChoiceField(required=False,
            label="IP version", choices=(('4','IPv4'), ('6','IPv6')))
    use_mirror_status = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        countries = Mirror.objects.filter(active=True).values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['country'].choices = [('all','All')] + make_choice(
                countries)
        self.fields['country'].initial = ['all']
        protos = make_choice(
                MirrorProtocol.objects.filter(is_download=True))
        initial = MirrorProtocol.objects.filter(is_download=True, default=True)
        self.fields['protocol'].choices = protos
        self.fields['protocol'].initial = [p.protocol for p in initial]
        self.fields['ip_version'].initial = ['4']

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

    return direct_to_template(request, 'mirrors/index.html',
            {'mirrorlist_form': form})

def find_mirrors(request, countries=None, protocols=None, use_status=False,
        ipv4_supported=True, ipv6_supported=True):
    if not protocols:
        protocols = MirrorProtocol.objects.filter(
                is_download=True).values_list('protocol', flat=True)
    qset = MirrorUrl.objects.select_related().filter(
            protocol__protocol__in=protocols,
            mirror__public=True, mirror__active=True,
    )
    if countries and 'all' not in countries:
        qset = qset.filter(Q(country__in=countries) |
                Q(mirror__country__in=countries))

    ip_version = Q()
    if ipv4_supported:
        ip_version |= Q(has_ipv4=True)
    if ipv6_supported:
        ip_version |= Q(has_ipv6=True)
    qset = qset.filter(ip_version)

    if not use_status:
        urls = qset.order_by('mirror__name', 'url')
        urls = sorted(urls, key=lambda x: x.real_country)
        template = 'mirrors/mirrorlist.txt'
    else:
        status_info = get_mirror_statuses()
        scores = dict([(u.id, u.score) for u in status_info['urls']])
        urls = []
        for u in qset:
            u.score = scores.get(u.id, None)
            # also include mirrors that don't have an up to date score
            # (as opposed to those that have been set with no score)
            if (u.id not in scores) or \
                    (u.score and u.score < 100.0):
                urls.append(u)
        # if a url doesn't have a score, treat it as the highest possible
        urls = sorted(urls, key=lambda x: x.score or 100.0)
        template = 'mirrors/mirrorlist_status.txt'

    return direct_to_template(request, template, {
                'mirror_urls': urls,
            },
            mimetype='text/plain')

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
    all_urls = sorted(all_urls, key=lambda x: x.url)

    return direct_to_template(request, 'mirrors/mirror_details.html',
            {'mirror': mirror, 'urls': all_urls})

def status(request):
    bad_timedelta = datetime.timedelta(days=3)
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
        'good_urls': good_urls,
        'bad_urls': bad_urls,
        'error_logs': get_mirror_errors(),
    })
    return direct_to_template(request, 'mirrors/status.html', context)

class MirrorStatusJSONEncoder(DjangoJSONEncoder):
    '''Base JSONEncoder extended to handle datetime.timedelta and MirrorUrl
    serialization. The base class takes care of datetime.datetime types.'''
    url_attributes = ['url', 'protocol', 'last_sync', 'completion_pct',
            'delay', 'duration_avg', 'duration_stddev', 'score']

    def default(self, obj):
        if isinstance(obj, datetime.timedelta):
            # always returned as integer seconds
            return obj.days * 24 * 3600 + obj.seconds
        if hasattr(obj, '__iter__'):
            # mainly for queryset serialization
            return list(obj)
        if isinstance(obj, MirrorUrl):
            data = dict((attr, getattr(obj, attr))
                    for attr in self.url_attributes)
            # separate because it isn't on the URL directly
            data['country'] = obj.real_country
            return data
        if isinstance(obj, MirrorProtocol):
            return unicode(obj)
        return super(MirrorStatusJSONEncoder, self).default(obj)

def status_json(request):
    status_info = get_mirror_statuses()
    data = status_info.copy()
    data['version'] = 2
    to_json = simplejson.dumps(data, ensure_ascii=False,
            cls=MirrorStatusJSONEncoder)
    response = HttpResponse(to_json, mimetype='application/json')
    return response

# vim: set ts=4 sw=4 et:

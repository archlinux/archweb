from django import forms
from django.db.models import Avg, Count, Max, Min, StdDev
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template

from main.utils import make_choice
from .models import Mirror, MirrorUrl, MirrorProtocol
from .utils import get_mirror_statuses, get_mirror_errors

import datetime
from operator import attrgetter

class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)
    protocol = forms.MultipleChoiceField(required=False)
    use_mirror_status = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        mirrors = Mirror.objects.filter(active=True).values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['country'].choices = [('all','All')] + make_choice(
                mirrors)
        self.fields['country'].initial = ['all']
        protos = make_choice(
                MirrorProtocol.objects.filter(is_download=True))
        self.fields['protocol'].choices = protos
        self.fields['protocol'].initial = [t[0] for t in protos]

@csrf_exempt
def generate_mirrorlist(request):
    if request.REQUEST.get('country', ''):
        form = MirrorlistForm(data=request.REQUEST)
        if form.is_valid():
            countries = form.cleaned_data['country']
            protocols = form.cleaned_data['protocol']
            use_status = form.cleaned_data['use_mirror_status']
            return find_mirrors(request, countries, protocols, use_status)
    else:
        form = MirrorlistForm()

    return direct_to_template(request, 'mirrors/index.html', {'mirrorlist_form': form})

def find_mirrors(request, countries=None, protocols=None, use_status=False):
    if not protocols:
        protocols = MirrorProtocol.objects.filter(
                is_download=True).values_list('protocol', flat=True)
    qset = MirrorUrl.objects.select_related().filter(
            protocol__protocol__in=protocols,
            mirror__public=True, mirror__active=True, mirror__isos=True
    )
    if countries and 'all' not in countries:
        qset = qset.filter(mirror__country__in=countries)
    if not use_status:
        urls = qset.order_by('mirror__country', 'mirror__name', 'url')
        template = 'mirrors/mirrorlist.txt'
    else:
        status_info = get_mirror_statuses()
        scores = dict([(u.id, u.score) for u in status_info['urls']])
        urls = []
        for u in qset:
            u.score = scores[u.id]
            if u.score and u.score < 100.0:
                urls.append(u)
        urls = sorted(urls, key=attrgetter('score'))
        template = 'mirrors/mirrorlist_status.txt'

    return direct_to_template(request, template, {
                'mirror_urls': urls,
            },
            mimetype='text/plain')

def mirrors(request):
    mirrors = Mirror.objects.select_related().order_by('tier', 'country')
    if not request.user.is_authenticated():
        mirrors = mirrors.filter(public=True, active=True)
    return direct_to_template(request, 'mirrors/mirrors.html',
            {'mirror_list': mirrors})

def mirror_details(request, name):
    mirror = get_object_or_404(Mirror, name=name)
    if not request.user.is_authenticated() and \
            (not mirror.public or not mirror.active):
        # TODO: maybe this should be 403? but that would leak existence
        raise Http404
    return direct_to_template(request, 'mirrors/mirror_details.html',
            {'mirror': mirror})

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

# vim: set ts=4 sw=4 et:

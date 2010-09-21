from django import forms
from django.db.models import Avg, Count, Max, Min, StdDev
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template

from main.utils import make_choice
from .models import Mirror, MirrorUrl, MirrorProtocol
from .models import MirrorLog

import datetime

class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)
    protocol = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        mirrors = Mirror.objects.filter(active=True).values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['country'].choices = make_choice(mirrors)
        self.fields['country'].initial = ['Any']
        protos = make_choice(
                MirrorProtocol.objects.exclude(protocol__iexact='rsync'))
        self.fields['protocol'].choices = protos
        self.fields['protocol'].initial = [t[0] for t in protos]

@csrf_exempt
def generate_mirrorlist(request):
    if request.REQUEST.get('country', ''):
        form = MirrorlistForm(data=request.REQUEST)
        if form.is_valid():
            countries = form.cleaned_data['country']
            protocols = form.cleaned_data['protocol']
            return find_mirrors(request, countries, protocols)
    else:
        form = MirrorlistForm()

    return direct_to_template(request, 'mirrors/index.html', {'mirrorlist_form': form})

def find_mirrors(request, countries=None, protocols=None):
    if not protocols:
        protocols = MirrorProtocol.objects.exclude(
                protocol__iexact='rsync').values_list('protocol', flat=True)
    qset = MirrorUrl.objects.select_related().filter(
            protocol__protocol__in=protocols,
            mirror__public=True, mirror__active=True, mirror__isos=True
    )
    if countries and 'all' not in countries:
        qset = qset.filter(mirror__country__in=countries)
    qset = qset.order_by('mirror__country', 'mirror__name', 'url')
    return direct_to_template(request, 'mirrors/mirrorlist.txt', {
                'mirror_urls': qset,
            },
            mimetype='text/plain')

def status(request):
    cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    bad_timedelta = datetime.timedelta(days=3)

    protocols = MirrorProtocol.objects.exclude(protocol__iexact='rsync')
    # I swear, this actually has decent performance...
    urls = MirrorUrl.objects.select_related(
            'mirror', 'protocol').filter(
            mirror__active=True, mirror__public=True,
            protocol__in=protocols).filter(
            logs__check_time__gte=cutoff_time).annotate(
            check_count=Count('logs'), last_sync=Max('logs__last_sync'),
            last_check=Max('logs__check_time'),
            duration_avg=Avg('logs__duration'), duration_min=Min('logs__duration'),
            duration_max=Max('logs__duration'), duration_stddev=StdDev('logs__duration')
            ).order_by('-last_sync', '-duration_avg')
    # errors during check process go in another table
    error_logs = MirrorLog.objects.filter(
            is_success=False, check_time__gte=cutoff_time).values(
            'url__url', 'url__protocol__protocol', 'url__mirror__country',
            'error').annotate(
            error_count=Count('error'), last_occurred=Max('check_time')
            ).order_by('-last_occurred', '-error_count')

    last_check = max([u.last_check for u in urls])

    good_urls = []
    bad_urls = []
    for url in urls:
        if url.last_check and url.last_sync:
            d = url.last_check - url.last_sync
            url.delay = d
            url.score = d.days * 24 + d.seconds / 3600 + url.duration_avg + url.duration_stddev
        else:
            url.delay = None
            url.score = None
        # split them into good and bad lists based on delay
        if not url.delay or url.delay > bad_timedelta:
            bad_urls.append(url)
        else:
            good_urls.append(url)

    context = {
        'last_check': last_check,
        'good_urls': good_urls,
        'bad_urls': bad_urls,
        'error_logs': error_logs,
    }
    return direct_to_template(request, 'mirrors/status.html', context)

# vim: set ts=4 sw=4 et:

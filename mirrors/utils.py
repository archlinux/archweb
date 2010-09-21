from django.db.models import Avg, Count, Max, Min, StdDev

from main.utils import cache_function
from .models import MirrorLog, MirrorProtocol, MirrorUrl

import datetime

cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=24)

@cache_function(300)
def get_mirror_statuses():
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

    for url in urls:
        if url.last_check and url.last_sync:
            d = url.last_check - url.last_sync
            url.delay = d
            url.score = d.days * 24 + d.seconds / 3600 + url.duration_avg + url.duration_stddev
        else:
            url.delay = None
            url.score = None
    return urls

@cache_function(300)
def get_mirror_errors():
    errors = MirrorLog.objects.filter(
            is_success=False, check_time__gte=cutoff_time).values(
            'url__url', 'url__protocol__protocol', 'url__mirror__country',
            'error').annotate(
            error_count=Count('error'), last_occurred=Max('check_time')
            ).order_by('-last_occurred', '-error_count')
    return list(errors)

# vim: set ts=4 sw=4 et:

from django.db.models import Avg, Count, Max, Min, StdDev

from main.utils import cache_function
from .models import MirrorLog, MirrorProtocol, MirrorUrl

import datetime

default_cutoff = datetime.timedelta(hours=24)

@cache_function(300)
def get_mirror_statuses(cutoff=default_cutoff):
    cutoff_time = datetime.datetime.utcnow() - cutoff
    protocols = list(MirrorProtocol.objects.filter(is_download=True))
    # I swear, this actually has decent performance...
    urls = MirrorUrl.objects.select_related('mirror', 'protocol').filter(
            mirror__active=True, mirror__public=True,
            protocol__in=protocols,
            logs__check_time__gte=cutoff_time).annotate(
            check_count=Count('logs'),
            success_count=Count('logs__duration'),
            last_sync=Max('logs__last_sync'),
            last_check=Max('logs__check_time'),
            duration_avg=Avg('logs__duration'),
            duration_stddev=StdDev('logs__duration')
            ).order_by('-last_sync', '-duration_avg')

    # The Django ORM makes it really hard to get actual average delay in the
    # above query, so run a seperate query for it and we will process the
    # results here.
    times = MirrorLog.objects.filter(is_success=True, last_sync__isnull=False,
            check_time__gte=cutoff_time)
    delays = {}
    for log in times:
        d = log.check_time - log.last_sync
        delays.setdefault(log.url_id, []).append(d)

    if urls:
        last_check = max([u.last_check for u in urls])
        num_checks = max([u.check_count for u in urls])
        check_info = MirrorLog.objects.filter(
                check_time__gte=cutoff_time).aggregate(
                mn=Min('check_time'), mx=Max('check_time'))
        if num_checks > 1:
            check_frequency = (check_info['mx'] - check_info['mn']) \
                    / (num_checks - 1)
        else:
            check_frequency = None;
    else:
        last_check = None
        num_checks = 0
        check_frequency = None

    for url in urls:
        url.completion_pct = float(url.success_count) / num_checks
        if url.id in delays:
            url_delays = delays[url.id]
            d = sum(url_delays, datetime.timedelta()) / len(url_delays)
            url.delay = d
            hours = d.days * 24.0 + d.seconds / 3600.0
            url.score = hours + url.duration_avg + url.duration_stddev
        else:
            url.delay = None
            url.score = None
            url.completion = 0.0

    return {
        'cutoff': cutoff,
        'last_check': last_check,
        'num_checks': num_checks,
        'check_frequency': check_frequency,
        'urls': urls,
    }

@cache_function(300)
def get_mirror_errors(cutoff=default_cutoff):
    cutoff_time = datetime.datetime.utcnow() - cutoff
    errors = MirrorLog.objects.filter(
            is_success=False, check_time__gte=cutoff_time,
            url__mirror__active=True, url__mirror__public=True).values(
            'url__url', 'url__protocol__protocol', 'url__mirror__country',
            'error').annotate(
            error_count=Count('error'), last_occurred=Max('check_time')
            ).order_by('-last_occurred', '-error_count')
    return list(errors)

# vim: set ts=4 sw=4 et:

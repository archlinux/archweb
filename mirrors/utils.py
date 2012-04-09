from datetime import timedelta

from django.db.models import Avg, Count, Max, Min, StdDev

from main.utils import cache_function, utc_now
from .models import MirrorLog, MirrorProtocol, MirrorUrl


default_cutoff = timedelta(hours=24)

def annotate_url(url, delays):
    '''Given a MirrorURL object, add a few more attributes to it regarding
    status, including completion_pct, delay, and score.'''
    url.completion_pct = float(url.success_count) / url.check_count
    if url.id in delays:
        url_delays = delays[url.id]
        url.delay = sum(url_delays, timedelta()) / len(url_delays)
        hours = url.delay.days * 24.0 + url.delay.seconds / 3600.0

        if url.completion_pct > 0:
            divisor = url.completion_pct
        else:
            # arbitrary small value
            divisor = 0.005
        url.score = (hours + url.duration_avg + url.duration_stddev) / divisor
    else:
        url.delay = None
        url.score = None


@cache_function(123)
def get_mirror_statuses(cutoff=default_cutoff):
    cutoff_time = utc_now() - cutoff
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
        delay = log.check_time - log.last_sync
        delays.setdefault(log.url_id, []).append(delay)

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
            check_frequency = None
    else:
        last_check = None
        num_checks = 0
        check_frequency = None

    for url in urls:
        annotate_url(url, delays)

    return {
        'cutoff': cutoff,
        'last_check': last_check,
        'num_checks': num_checks,
        'check_frequency': check_frequency,
        'urls': urls,
    }


@cache_function(117)
def get_mirror_errors(cutoff=default_cutoff):
    cutoff_time = utc_now() - cutoff
    errors = MirrorLog.objects.filter(
            is_success=False, check_time__gte=cutoff_time,
            url__mirror__active=True, url__mirror__public=True).values(
            'url__url', 'url__country', 'url__protocol__protocol',
            'url__mirror__country', 'error').annotate(
            error_count=Count('error'), last_occurred=Max('check_time')
            ).order_by('-last_occurred', '-error_count')
    errors = list(errors)
    for err in errors:
        err['country'] = err['url__country'] or err['url__mirror__country']
    return errors


@cache_function(295)
def get_mirror_url_for_download(cutoff=default_cutoff):
    '''Find a good mirror URL to use for package downloads. If we have mirror
    status data available, it is used to determine a good choice by looking at
    the last batch of status rows.'''
    cutoff_time = utc_now() - cutoff
    status_data = MirrorLog.objects.filter(
            check_time__gte=cutoff_time).aggregate(
            Max('check_time'), Max('last_sync'))
    if status_data['check_time__max'] is not None:
        min_check_time = status_data['check_time__max'] - timedelta(minutes=5)
        min_sync_time = status_data['last_sync__max'] - timedelta(minutes=30)
        best_logs = MirrorLog.objects.filter(is_success=True,
                check_time__gte=min_check_time, last_sync__gte=min_sync_time,
                url__mirror__public=True, url__mirror__active=True,
                url__protocol__protocol__iexact='HTTP').order_by(
                'duration')[:1]
        if best_logs:
            return MirrorUrl.objects.get(id=best_logs[0].url_id)

    mirror_urls = MirrorUrl.objects.filter(
            mirror__public=True, mirror__active=True,
            protocol__protocol__iexact='HTTP')
    # look first for an 'Any' URL, then fall back to any HTTP URL
    filtered_urls = mirror_urls.filter(mirror__country='Any')[:1]
    if not filtered_urls:
        filtered_urls = mirror_urls[:1]
    if not filtered_urls:
        return None
    return filtered_urls[0]

# vim: set ts=4 sw=4 et:

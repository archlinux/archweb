from datetime import timedelta

from django.db.models import Avg, Count, Max, Min, StdDev
from django.utils.timezone import now
from django_countries.fields import Country

from main.utils import cache_function, database_vendor
from .models import MirrorLog, MirrorProtocol, MirrorUrl


DEFAULT_CUTOFF = timedelta(hours=24)

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
def get_mirror_statuses(cutoff=DEFAULT_CUTOFF, mirror_ids=None):
    cutoff_time = now() - cutoff
    url_data = MirrorUrl.objects.values('id', 'mirror_id').filter(
            mirror__active=True, mirror__public=True,
            logs__check_time__gte=cutoff_time).annotate(
            check_count=Count('logs'),
            success_count=Count('logs__duration'),
            last_sync=Max('logs__last_sync'),
            last_check=Max('logs__check_time'),
            duration_avg=Avg('logs__duration'))

    vendor = database_vendor(MirrorUrl)
    if vendor != 'sqlite':
        url_data = url_data.annotate(duration_stddev=StdDev('logs__duration'))

    urls = MirrorUrl.objects.select_related('mirror', 'protocol').filter(
            mirror__active=True, mirror__public=True,
            logs__check_time__gte=cutoff_time).distinct().order_by(
            'mirror__id', 'url')

    if mirror_ids:
        url_data = url_data.filter(mirror_id__in=mirror_ids)
        urls = urls.filter(mirror_id__in=mirror_ids)

    # The Django ORM makes it really hard to get actual average delay in the
    # above query, so run a seperate query for it and we will process the
    # results here.
    times = MirrorLog.objects.values_list(
            'url_id', 'check_time', 'last_sync').filter(
            is_success=True, last_sync__isnull=False,
            check_time__gte=cutoff_time)
    if mirror_ids:
        times = times.filter(url__mirror_id__in=mirror_ids)
    delays = {}
    for url_id, check_time, last_sync in times:
        delay = check_time - last_sync
        delays.setdefault(url_id, []).append(delay)

    if urls:
        url_data = dict((item['id'], item) for item in url_data)
        for url in urls:
            for k, v in url_data.get(url.id, {}).items():
                if k not in ('id', 'mirror_id'):
                    setattr(url, k, v)
        last_check = max([u.last_check for u in urls])
        num_checks = max([u.check_count for u in urls])
        check_info = MirrorLog.objects.filter(check_time__gte=cutoff_time)
        if mirror_ids:
            check_info = check_info.filter(url__mirror_id__in=mirror_ids)
        check_info = check_info.aggregate(
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
        # fake the standard deviation for local testing setups
        if vendor == 'sqlite':
            setattr(url, 'duration_stddev', 0.0)
        annotate_url(url, delays)

    return {
        'cutoff': cutoff,
        'last_check': last_check,
        'num_checks': num_checks,
        'check_frequency': check_frequency,
        'urls': urls,
    }


@cache_function(117)
def get_mirror_errors(cutoff=DEFAULT_CUTOFF, mirror_ids=None):
    cutoff_time = now() - cutoff
    errors = MirrorLog.objects.filter(
            is_success=False, check_time__gte=cutoff_time,
            url__mirror__active=True, url__mirror__public=True).values(
            'url__url', 'url__country', 'url__protocol__protocol',
            'url__mirror__country', 'url__mirror__tier', 'error').annotate(
            error_count=Count('error'), last_occurred=Max('check_time')
            ).order_by('-last_occurred', '-error_count')

    if mirror_ids:
        urls = urls.filter(mirror_id__in=mirror_ids)

    errors = list(errors)
    for err in errors:
        ctry_code = err['url__country'] or err['url__mirror__country']
        err['country'] = Country(ctry_code)
    return errors


@cache_function(295)
def get_mirror_url_for_download(cutoff=DEFAULT_CUTOFF):
    '''Find a good mirror URL to use for package downloads. If we have mirror
    status data available, it is used to determine a good choice by looking at
    the last batch of status rows.'''
    cutoff_time = now() - cutoff
    status_data = MirrorLog.objects.filter(
            check_time__gte=cutoff_time).aggregate(
            Max('check_time'), Max('last_sync'))
    if status_data['check_time__max'] is not None:
        min_check_time = status_data['check_time__max'] - timedelta(minutes=5)
        min_sync_time = status_data['last_sync__max'] - timedelta(minutes=20)
        best_logs = MirrorLog.objects.filter(is_success=True,
                check_time__gte=min_check_time, last_sync__gte=min_sync_time,
                url__mirror__public=True, url__mirror__active=True,
                url__protocol__default=True).order_by(
                'duration')[:1]
        if best_logs:
            return MirrorUrl.objects.get(id=best_logs[0].url_id)

    mirror_urls = MirrorUrl.objects.filter(
            mirror__public=True, mirror__active=True, protocol__default=True)
    # look first for a country-agnostic URL, then fall back to any HTTP URL
    filtered_urls = mirror_urls.filter(mirror__country='')[:1]
    if not filtered_urls:
        filtered_urls = mirror_urls[:1]
    if not filtered_urls:
        return None
    return filtered_urls[0]

# vim: set ts=4 sw=4 et:

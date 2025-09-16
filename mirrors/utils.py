from datetime import timedelta

from django.db import connection
from django.db.models import Count, Max, Min
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from main.utils import cache_function, database_vendor

from .models import MirrorLog, MirrorUrl

DEFAULT_CUTOFF = timedelta(hours=24)


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict."
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row, strict=False))
        for row in cursor.fetchall()
    ]


def status_data(cutoff_time, mirror_id=None):
    if mirror_id is not None:
        params = [cutoff_time, mirror_id]
        mirror_where = 'AND u.mirror_id = %s'
    else:
        params = [cutoff_time]
        mirror_where = ''

    vendor = database_vendor(MirrorUrl)
    if vendor == 'sqlite':
        sql = """
SELECT l.url_id, u.mirror_id,
    COUNT(l.id) AS check_count,
    COUNT(l.last_sync) AS success_count,
    MAX(l.last_sync) AS last_sync,
    MAX(l.check_time) AS last_check,
    AVG(l.duration) AS duration_avg,
    0.0 AS duration_stddev,
    AVG(STRFTIME('%%s', check_time) - STRFTIME('%%s', last_sync)) AS delay
FROM mirrors_mirrorlog l
JOIN mirrors_mirrorurl u ON u.id = l.url_id
WHERE l.check_time >= %s
""" + mirror_where + """
GROUP BY l.url_id, u.mirror_id
"""
    else:
        sql = """
SELECT l.url_id, u.mirror_id,
    COUNT(l.id) AS check_count,
    COUNT(l.last_sync) AS success_count,
    MAX(l.last_sync) AS last_sync,
    MAX(l.check_time) AS last_check,
    AVG(l.duration) AS duration_avg,
    STDDEV(l.duration) AS duration_stddev,
    AVG(check_time - last_sync) AS delay
FROM mirrors_mirrorlog l
JOIN mirrors_mirrorurl u ON u.id = l.url_id
WHERE l.check_time >= %s
""" + mirror_where + """
GROUP BY l.url_id, u.mirror_id
"""

    cursor = connection.cursor()
    cursor.execute(sql, params)
    url_data = dictfetchall(cursor)

    # sqlite loves to return less than ideal types
    if vendor == 'sqlite':
        for item in url_data:
            if item['delay'] is not None:
                item['delay'] = timedelta(seconds=item['delay'])
            if item['last_sync'] is not None:
                item['last_sync'] = parse_datetime(item['last_sync'])
            item['last_check'] = parse_datetime(item['last_check'])

    return {item['url_id']: item for item in url_data}


def annotate_url(url, url_data):
    '''Given a MirrorURL object, add a few more attributes to it regarding
    status, including completion_pct, delay, and score.'''
    # set up some sane default values in case we are missing anything
    url.success_count = 0
    url.check_count = 0
    url.completion_pct = None
    url.duration_avg = None
    url.duration_stddev = None
    url.last_check = None
    url.last_sync = None
    url.delay = None
    url.score = None
    for k, v in url_data.items():
        if k not in ('url_id', 'mirror_id'):
            setattr(url, k, v)

    if url.check_count > 0:
        url.completion_pct = float(url.success_count) / url.check_count

    if url.delay is not None:
        hours = url.delay.days * 24.0 + url.delay.seconds / 3600.0

        if url.completion_pct > 0.0:
            divisor = url.completion_pct
        else:
            # arbitrary small value
            divisor = 0.005
        stddev = url.duration_stddev or 0.0
        url.score = (hours + url.duration_avg + stddev) / divisor

    return url


@cache_function(178)
def get_mirror_statuses(cutoff=DEFAULT_CUTOFF, mirror_id=None, show_all=False):
    cutoff_time = now() - cutoff

    urls = MirrorUrl.objects.select_related(
        'mirror', 'protocol').order_by('mirror__id', 'url')
    if mirror_id:
        urls = urls.filter(mirror_id=mirror_id)
    if not show_all:
        urls = urls.filter(active=True, mirror__active=True, mirror__public=True)

    if urls:
        url_data = status_data(cutoff_time, mirror_id)
        urls = [annotate_url(url, url_data.get(url.id, {})) for url in urls]
        last_check = max([u.last_check for u in urls if u.last_check] or [None])
        num_checks = max(u.check_count for u in urls)
        check_info = MirrorLog.objects.filter(check_time__gte=cutoff_time)
        if mirror_id:
            check_info = check_info.filter(url__mirror_id=mirror_id)
        check_info = check_info.aggregate(
            mn=Min('check_time'), mx=Max('check_time'))
        if num_checks > 1:
            check_frequency = (check_info['mx'] - check_info['mn']) \
                / (num_checks - 1)
        else:
            check_frequency = None
    else:
        urls = []
        last_check = None
        num_checks = 0
        check_frequency = None

    return {
        'cutoff': cutoff,
        'last_check': last_check,
        'num_checks': num_checks,
        'check_frequency': check_frequency,
        'urls': urls,
    }


def get_mirror_errors(cutoff=DEFAULT_CUTOFF, mirror_id=None, show_all=False):
    cutoff_time = now() - cutoff
    errors = MirrorLog.objects.filter(
        is_success=False, check_time__gte=cutoff_time,  url__mirror__public=True).values(
        'url__id', 'error').annotate(
        error_count=Count('error'), last_occurred=Max('check_time')).order_by(
        '-last_occurred', '-error_count')

    if mirror_id:
        errors = errors.filter(url__mirror_id=mirror_id)
    if not show_all:
        errors = errors.filter(
            url__active=True, url__mirror__active=True, url__mirror__public=True)

    errors = list(errors)
    to_fetch = [err['url__id'] for err in errors]
    urls = MirrorUrl.objects.select_related(
        'mirror', 'protocol').in_bulk(to_fetch)
    for err in errors:
        err['url'] = urls[err['url__id']]
    return errors


@cache_function(295)
def get_mirror_url_for_download(cutoff=DEFAULT_CUTOFF):
    '''Find a good mirror URL to use for package downloads. If we have mirror
    status data available, it is used to determine a good choice by looking at
    the last batch of status rows.'''
    cutoff_time = now() - cutoff
    log_data = MirrorLog.objects.filter(
        check_time__gte=cutoff_time).aggregate(
        Max('check_time'), Max('last_sync'))
    if log_data['check_time__max'] is not None:
        min_check_time = log_data['check_time__max'] - timedelta(minutes=5)
        min_sync_time = log_data['last_sync__max'] - timedelta(minutes=20)
        best_logs = MirrorLog.objects.select_related('url').filter(
            is_success=True,
            check_time__gte=min_check_time, last_sync__gte=min_sync_time,
            url__active=True,
            url__mirror__public=True, url__mirror__active=True,
            url__protocol__default=True,
            url__protocol__protocol='https').order_by(
            'duration')[:1]
        if best_logs:
            return best_logs[0].url

    mirror_urls = MirrorUrl.objects.filter(active=True, mirror__public=True,
                                           mirror__active=True,
                                           protocol__protocol='https',
                                           protocol__default=True)[:1]
    if not mirror_urls:
        return None
    return mirror_urls[0]

# vim: set ts=4 sw=4 et:

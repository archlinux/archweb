from datetime import timedelta
from itertools import groupby
from operator import attrgetter, itemgetter

from django.db import connection
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from django.views.decorators.http import condition
from django_countries.fields import Country

from ..models import Mirror, MirrorUrl, MirrorLog
from ..utils import get_mirror_statuses, get_mirror_errors


def mirrors(request, tier=None):
    mirror_list = Mirror.objects.select_related().order_by('tier', 'name')
    if tier is not None:
        tier = int(tier)
        if tier not in [t[0] for t in Mirror.TIER_CHOICES]:
            raise Http404
        mirror_list = mirror_list.filter(tier=tier)
    protos = MirrorUrl.objects.values_list(
        'mirror_id', 'protocol__protocol').order_by(
        'mirror_id', 'protocol__protocol').distinct()
    countries = MirrorUrl.objects.values_list(
        'mirror_id', 'country').order_by(
        'mirror_id', 'country').distinct()

    if not request.user.is_authenticated:
        mirror_list = mirror_list.filter(public=True, active=True)
        protos = protos.filter(
            mirror__public=True, mirror__active=True, active=True)
        countries = countries.filter(
            mirror__public=True, mirror__active=True, active=True)

    protos = {k: list(v) for k, v in groupby(protos, key=itemgetter(0))}
    countries = {k: list(v) for k, v in groupby(countries, key=itemgetter(0))}

    for mirror in mirror_list:
        item_protos = protos.get(mirror.id, [])
        mirror.protocols = [item[1] for item in item_protos]
        mirror.country = None
        item_countries = countries.get(mirror.id, [])
        if len(item_countries) == 1:
            mirror.country = Country(item_countries[0][1])

    return render(request, 'mirrors/mirrors.html',
                  {'mirror_list': mirror_list})


def mirror_details(request, name):
    mirror = get_object_or_404(Mirror, name=name)
    authorized = request.user.is_authenticated
    if not authorized and \
            (not mirror.public or not mirror.active):
        raise Http404
    error_cutoff = timedelta(days=7)

    status_info = get_mirror_statuses(mirror_id=mirror.id, show_all=authorized)
    checked_urls = {url for url in status_info['urls'] if url.mirror_id == mirror.id}
    all_urls = mirror.urls.select_related('protocol')
    if not authorized:
        all_urls = all_urls.filter(active=True)
    all_urls = set(all_urls)
    # Add dummy data for URLs that we haven't checked recently
    other_urls = all_urls.difference(checked_urls)
    for url in other_urls:
        for attr in ('last_sync', 'completion_pct', 'delay', 'duration_avg',
                     'duration_stddev', 'score'):
            setattr(url, attr, None)
    all_urls = sorted(checked_urls.union(other_urls), key=attrgetter('url'))

    error_logs = get_mirror_errors(mirror_id=mirror.id, cutoff=error_cutoff,
                                   show_all=True)

    context = {
        'mirror': mirror,
        'urls': all_urls,
        'cutoff': error_cutoff,
        'error_logs': error_logs,
    }
    return render(request, 'mirrors/mirror_details.html', context)


def url_details(request, name, url_id):
    url = get_object_or_404(MirrorUrl.objects.select_related(),
                            id=url_id, mirror__name=name)
    mirror = url.mirror
    authorized = request.user.is_authenticated
    if not authorized and \
            (not mirror.public or not mirror.active or not url.active):
        raise Http404
    error_cutoff = timedelta(days=7)
    cutoff_time = now() - error_cutoff
    logs = MirrorLog.objects.select_related('location').filter(
        url=url, check_time__gte=cutoff_time).order_by('-check_time')

    context = {
        'url': url,
        'logs': logs,
    }
    return render(request, 'mirrors/url_details.html', context)


def status_last_modified(request, *args, **kwargs):
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(check_time) FROM mirrors_mirrorlog")
    return cursor.fetchone()[0]


@condition(last_modified_func=status_last_modified)
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
        if url.completion_pct is None:
            # skip URLs that have never been checked
            continue
        elif not url.delay or url.delay > bad_timedelta:
            bad_urls.append(url)
        else:
            good_urls.append(url)

    error_logs = get_mirror_errors()
    if tier is not None:
        error_logs = [log for log in error_logs if log['url'].mirror.tier == tier]

    context = status_info.copy()
    context.update({
        'good_urls': sorted(good_urls, key=attrgetter('score')),
        'bad_urls': sorted(bad_urls, key=lambda u: u.delay or timedelta.max),
        'error_logs': error_logs,
        'tier': tier,
    })
    return render(request, 'mirrors/status.html', context)

# vim: set ts=4 sw=4 et:

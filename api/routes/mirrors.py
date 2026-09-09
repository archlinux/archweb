from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from ninja import Router

from api.schemas.mirrors import (
    MirrorDetailsSchema,
    MirrorLocationSchema,
    MirrorLocationsSchema,
    MirrorLogSchema,
    MirrorStatusSchema,
    MirrorUrlSchema,
    MirrorUrlWithLogsSchema,
)
from mirrors.models import CheckLocation, Mirror
from mirrors.utils import DEFAULT_CUTOFF, get_mirror_statuses

router = Router(tags=["mirrors"])


def _td_seconds(value) -> int:
    return value.days * 24 * 3600 + value.seconds


def _td_seconds_or_none(value) -> int | None:
    if value is None:
        return None
    return _td_seconds(value)


def _url_to_schema(url) -> MirrorUrlSchema:
    return MirrorUrlSchema(
        url=url.url,
        protocol=str(url.protocol),
        last_sync=url.last_sync,
        completion_pct=url.completion_pct,
        delay=_td_seconds_or_none(url.delay),
        duration_avg=url.duration_avg,
        duration_stddev=url.duration_stddev,
        score=url.score,
        active=url.active,
        country=str(url.country.name),
        country_code=url.country.code,
        isos=url.mirror.isos,
        ipv4=url.has_ipv4,
        ipv6=url.has_ipv6,
        details=url.get_full_url(),
    )


def _url_with_logs_to_schema(url, cutoff_time) -> MirrorUrlWithLogsSchema:
    base = _url_to_schema(url)
    logs = [
        MirrorLogSchema(
            check_time=log.check_time,
            last_sync=log.last_sync,
            duration=log.duration,
            is_success=log.is_success,
            location_id=log.location_id,
            error=log.error or None,
        )
        for log in url.logs.filter(check_time__gte=cutoff_time).order_by('check_time')
    ]
    return MirrorUrlWithLogsSchema(**base.dict(), logs=logs)


@router.get("/status/", response=MirrorStatusSchema, url_name="mirror-status")
def status(request):
    info = get_mirror_statuses()
    return MirrorStatusSchema(
        version=3,
        urls=[_url_to_schema(u) for u in info['urls']],
        cutoff=_td_seconds(info["cutoff"]),
        last_check=info['last_check'],
        num_checks=info['num_checks'],
        check_frequency=_td_seconds_or_none(info["check_frequency"]),
    )


@router.get("/status/tier/{tier}/", response=MirrorStatusSchema, url_name="mirror-status-tier")
def status_tier(request, tier: int):
    if tier not in [t[0] for t in Mirror.TIER_CHOICES]:
        raise Http404
    info = get_mirror_statuses()
    urls = [u for u in info['urls'] if u.mirror.tier == tier]
    return MirrorStatusSchema(
        version=3,
        urls=[_url_to_schema(u) for u in urls],
        cutoff=_td_seconds(info["cutoff"]),
        last_check=info['last_check'],
        num_checks=info['num_checks'],
        check_frequency=_td_seconds_or_none(info["check_frequency"]),
    )


@router.get("/locations/", response=MirrorLocationsSchema, url_name="mirror-locations")
def locations(request):
    return MirrorLocationsSchema(
        version=1,
        locations=[
            MirrorLocationSchema(
                id=loc.pk,
                hostname=loc.hostname,
                source_ip=loc.source_ip,
                country=str(loc.country.name),
                country_code=loc.country.code,
                ip_version=loc.ip_version,
            )
            for loc in CheckLocation.objects.all().order_by('pk')
        ],
    )


@router.get("/{name}/", response=MirrorDetailsSchema, url_name="mirror-details")
def mirror_details(request, name: str):
    authorized = request.user.is_authenticated
    mirror = get_object_or_404(Mirror, name=name)
    if not authorized and (not mirror.public or not mirror.active):
        raise Http404
    info = get_mirror_statuses(mirror_id=mirror.id, show_all=authorized)
    cutoff_time = now() - DEFAULT_CUTOFF

    admin_email = None
    alternate_email = None
    if authorized and request.user.has_perm('mirrors.change_mirror'):
        admin_email = mirror.admin_email
        alternate_email = mirror.alternate_email

    return MirrorDetailsSchema(
        version=5,
        tier=mirror.tier,
        upstream=mirror.upstream.name if mirror.upstream else None,
        details=mirror.get_full_url(),
        urls=[_url_with_logs_to_schema(u, cutoff_time) for u in info['urls']],
        cutoff=_td_seconds(info["cutoff"]),
        last_check=info['last_check'],
        num_checks=info['num_checks'],
        check_frequency=_td_seconds_or_none(info["check_frequency"]),
        admin_email=admin_email,
        alternate_email=alternate_email,
    )

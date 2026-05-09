from django.urls import reverse
from ninja import Router

from api.schemas.releng import ReleaseSchema, ReleasesSchema
from releng.models import Release

router = Router(tags=["releng"])


def _release_to_schema(release: Release) -> ReleaseSchema:
    return ReleaseSchema(
        version=release.version,
        kernel_version=release.kernel_version or None,
        release_date=release.release_date,
        available=release.available,
        info=release.info,
        iso_url='/' + release.iso_url(),
        magnet_uri=release.magnet_uri(),
        torrent_url=reverse('releng-release-torrent', args=[release.version]),
        md5_sum=release.md5_sum or None,
        sha1_sum=release.sha1_sum or None,
        sha256_sum=release.sha256_sum or None,
        b2_sum=release.b2_sum or None,
        wkd_email=release.wkd_email or None,
        pgp_fingerprint=release.pgp_key or None,
        created=release.created,
        last_modified=release.last_modified,
    )


@router.get("/releases/", response=ReleasesSchema, url_name="releng-releases")
def releases(request):
    all_releases = Release.objects.all()
    try:
        latest_version = Release.objects.filter(available=True).values_list(
            'version', flat=True).latest()
    except Release.DoesNotExist:
        latest_version = None

    return ReleasesSchema(
        version=1,
        releases=[_release_to_schema(r) for r in all_releases],
        latest_version=latest_version,
    )

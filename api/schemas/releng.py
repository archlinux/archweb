from datetime import date, datetime

from ninja import Schema


class ReleaseSchema(Schema):
    version: str
    kernel_version: str | None = None
    release_date: date
    available: bool
    info: str
    iso_url: str | None = None
    magnet_uri: str | None = None
    torrent_url: str | None = None
    md5_sum: str | None = None
    sha1_sum: str | None = None
    sha256_sum: str | None = None
    b2_sum: str | None = None
    wkd_email: str | None = None
    pgp_fingerprint: str | None = None
    created: datetime
    last_modified: datetime


class ReleasesSchema(Schema):
    version: int
    releases: list[ReleaseSchema]
    latest_version: str | None = None

from datetime import date, datetime
from typing import Optional

from ninja import Schema


class ReleaseSchema(Schema):
    version: str
    kernel_version: Optional[str] = None
    release_date: date
    available: bool
    info: str
    iso_url: Optional[str] = None
    magnet_uri: Optional[str] = None
    torrent_url: Optional[str] = None
    md5_sum: Optional[str] = None
    sha1_sum: Optional[str] = None
    sha256_sum: Optional[str] = None
    b2_sum: Optional[str] = None
    wkd_email: Optional[str] = None
    pgp_fingerprint: Optional[str] = None
    created: datetime
    last_modified: datetime


class ReleasesSchema(Schema):
    version: int
    releases: list[ReleaseSchema]
    latest_version: Optional[str] = None

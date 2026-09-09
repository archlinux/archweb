from datetime import datetime

from ninja import Schema


class MirrorLogSchema(Schema):
    check_time: datetime
    last_sync: datetime | None = None
    duration: float | None = None
    is_success: bool
    location_id: int | None = None
    error: str | None = None


class MirrorUrlSchema(Schema):
    url: str
    protocol: str
    last_sync: datetime | None = None
    completion_pct: float | None = None
    delay: int | None = None
    duration_avg: float | None = None
    duration_stddev: float | None = None
    score: float | None = None
    active: bool
    country: str
    country_code: str
    isos: bool
    ipv4: bool
    ipv6: bool
    details: str


class MirrorUrlWithLogsSchema(MirrorUrlSchema):
    logs: list[MirrorLogSchema] = []


class MirrorStatusSchema(Schema):
    version: int
    urls: list[MirrorUrlSchema]
    cutoff: int
    last_check: datetime | None = None
    num_checks: int
    check_frequency: int | None = None


class MirrorDetailsSchema(Schema):
    version: int
    tier: int
    upstream: str | None = None
    details: str
    urls: list[MirrorUrlWithLogsSchema]
    cutoff: int
    last_check: datetime | None = None
    num_checks: int
    check_frequency: int | None = None
    admin_email: str | None = None
    alternate_email: str | None = None


class MirrorLocationSchema(Schema):
    id: int
    hostname: str
    source_ip: str
    country: str
    country_code: str
    ip_version: int


class MirrorLocationsSchema(Schema):
    version: int
    locations: list[MirrorLocationSchema]

from datetime import datetime

from ninja import Schema


class PackageSchema(Schema):
    pkgname: str
    pkgbase: str
    repo: str
    arch: str
    pkgver: str
    pkgrel: str
    epoch: int
    pkgdesc: str | None = None
    url: str | None = None
    filename: str
    compressed_size: int
    installed_size: int
    build_date: datetime | None = None
    last_update: datetime
    flag_date: datetime | None = None
    maintainers: list[str]
    packager: str | None = None
    groups: list[str]
    licenses: list[str]
    conflicts: list[str]
    provides: list[str]
    replaces: list[str]
    depends: list[str]
    optdepends: list[str]
    makedepends: list[str]
    checkdepends: list[str]


class PackageFilesSchema(Schema):
    pkgname: str
    repo: str
    arch: str
    pkg_last_update: datetime
    files_last_update: datetime | None = None
    files_count: int
    dir_count: int
    files: list[str]


class PackageSearchSchema(Schema):
    version: int
    limit: int
    valid: bool
    results: list[PackageSchema]
    num_pages: int | None = None
    count: int | None = None
    page: int | None = None

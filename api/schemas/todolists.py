from datetime import datetime

from ninja import Schema

from api.schemas.packages import PackageSchema


class TodolistPackageSchema(PackageSchema):
    status_str: str


class TodolistSchema(Schema):
    id: int
    name: str
    description: str
    created: datetime
    last_modified: datetime
    packages: list[TodolistPackageSchema]
    kind: str

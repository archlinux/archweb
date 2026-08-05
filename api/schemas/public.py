from ninja import Schema


class PGPNodeSchema(Schema):
    name: str
    key: str | None = None
    group: str


class PGPEdgeSchema(Schema):
    signee: str
    signer: str


class PGPKeysSchema(Schema):
    nodes: list[PGPNodeSchema]
    edges: list[PGPEdgeSchema]

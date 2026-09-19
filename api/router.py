from ninja import NinjaAPI

from api.routes import mirrors, packages, public, releng, todolists

api = NinjaAPI(
    version="1",
    title="Archweb API",
    description="Arch Linux web API",
    openapi_url="/openapi.json",
    docs_url="/docs/",
)

api.add_router("/v1/releng/", releng.router)
api.add_router("/v1/mirrors/", mirrors.router)
api.add_router("/v1/master-keys/", public.router)
api.add_router("/v1/packages/", packages.router)
api.add_router("/v1/todo/", todolists.router)

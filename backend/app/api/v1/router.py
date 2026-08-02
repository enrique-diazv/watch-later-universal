from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    media,
    providers,
    search,
)

from app.api.v1.endpoints import (
    auth,
    health,
    library,
    media,
    providers,
    search,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(search.router)
api_router.include_router(media.router)
api_router.include_router(providers.router)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)

api_router.include_router(
    library.router,
    prefix="/library",
    tags=["library"],
)
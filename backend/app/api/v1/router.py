from fastapi import APIRouter

from app.api.v1.endpoints import health, media, providers, search


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(search.router)
api_router.include_router(media.router)
api_router.include_router(providers.router)
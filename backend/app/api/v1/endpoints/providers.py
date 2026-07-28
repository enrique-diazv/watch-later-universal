from typing import Annotated, Any

import httpx
from fastapi import APIRouter, HTTPException, Path

from app.core.config import get_settings
from app.integrations.tmdb.client import (
    MediaType,
    get_watch_providers,
)
from app.schemas.media import (
    AvailabilityType,
    WatchProvider,
    WatchProvidersResponse,
)


router = APIRouter()

LOGO_BASE_URL = "https://image.tmdb.org/t/p/w185"

AVAILABILITY_TYPES: tuple[AvailabilityType, ...] = (
    "flatrate",
    "free",
    "ads",
    "rent",
    "buy",
)


def transform_watch_providers(
    tmdb_response: dict[str, Any],
    media_type: MediaType,
    tmdb_id: int,
    region: str,
) -> WatchProvidersResponse:
    region_data = (
        tmdb_response
        .get("results", {})
        .get(region, {})
    )

    providers: list[WatchProvider] = []

    for availability_type in AVAILABILITY_TYPES:
        category_providers = (
            region_data.get(availability_type, []) or []
        )

        for item in category_providers:
            logo_path = item.get("logo_path")

            providers.append(
                WatchProvider(
                    tmdb_provider_id=item["provider_id"],
                    name=item["provider_name"],
                    logo_url=(
                        f"{LOGO_BASE_URL}{logo_path}"
                        if logo_path
                        else None
                    ),
                    display_priority=(
                        item.get("display_priority") or 0
                    ),
                    availability_type=availability_type,
                )
            )

    return WatchProvidersResponse(
        tmdb_id=tmdb_id,
        media_type=media_type,
        region=region,
        link=region_data.get("link"),
        providers=providers,
    )


@router.get(
    "/media/{media_type}/{tmdb_id}/providers",
    response_model=WatchProvidersResponse,
)
async def media_watch_providers(
    media_type: MediaType,
    tmdb_id: Annotated[int, Path(gt=0)],
) -> WatchProvidersResponse:
    settings = get_settings()
    region = settings.tmdb_region.upper()

    try:
        tmdb_response = await get_watch_providers(
            media_type,
            tmdb_id,
        )
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="TMDB tardó demasiado en responder.",
        ) from error
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Contenido no encontrado.",
            ) from error

        raise HTTPException(
            status_code=502,
            detail="TMDB respondió con un error.",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail="No fue posible conectar con TMDB.",
        ) from error

    return transform_watch_providers(
        tmdb_response=tmdb_response,
        media_type=media_type,
        tmdb_id=tmdb_id,
        region=region,
    )
from typing import Any, Literal

import httpx

from app.core.config import get_settings


MediaType = Literal["movie", "tv"]


async def _get(
    path: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()

    headers = {
        "Authorization": (
            f"Bearer {settings.tmdb_access_token.get_secret_value()}"
        ),
        "Accept": "application/json",
    }

    url = f"{settings.tmdb_base_url}/{path.lstrip('/')}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            url,
            headers=headers,
            params=params,
        )
        response.raise_for_status()

    return response.json()


async def search_multi(
    query: str,
    page: int = 1,
) -> dict[str, Any]:
    settings = get_settings()

    return await _get(
        path="search/multi",
        params={
            "query": query,
            "include_adult": False,
            "language": settings.tmdb_language,
            "page": page,
        },
    )


async def get_media_details(
    media_type: MediaType,
    tmdb_id: int,
) -> dict[str, Any]:
    settings = get_settings()

    return await _get(
        path=f"{media_type}/{tmdb_id}",
        params={
            "language": settings.tmdb_language,
        },
    )
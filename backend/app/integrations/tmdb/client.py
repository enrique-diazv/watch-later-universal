from typing import Any

import httpx

from app.core.config import get_settings


async def search_multi(query: str, page: int = 1) -> dict[str, Any]:
    settings = get_settings()

    headers = {
        "Authorization": (
            f"Bearer {settings.tmdb_access_token.get_secret_value()}"
        ),
        "accept": "application/json",
    }

    params = {
        "query": query,
        "include_adult": False,
        "language": settings.tmdb_language,
        "page": page,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.tmdb_base_url}/search/multi",
            headers=headers,
            params=params,
        )
        response.raise_for_status()

    return response.json()
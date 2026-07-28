from typing import Annotated, Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.integrations.tmdb.client import search_multi
from app.schemas.media import SearchResponse, SearchResult


router = APIRouter()

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


def extract_release_year(item: dict[str, Any]) -> int | None:
    date_field = (
        "release_date"
        if item.get("media_type") == "movie"
        else "first_air_date"
    )
    release_date = item.get(date_field)

    if not release_date:
        return None

    try:
        return int(release_date[:4])
    except (TypeError, ValueError):
        return None


def transform_result(item: dict[str, Any]) -> SearchResult | None:
    media_type = item.get("media_type")

    if media_type not in {"movie", "tv"}:
        return None

    title_field = "title" if media_type == "movie" else "name"
    title = item.get(title_field)

    if not title:
        return None

    poster_path = item.get("poster_path")

    return SearchResult(
        tmdb_id=item["id"],
        media_type=media_type,
        title=title,
        overview=item.get("overview") or "",
        poster_url=(
            f"{POSTER_BASE_URL}{poster_path}"
            if poster_path
            else None
        ),
        release_year=extract_release_year(item),
        rating=item.get("vote_average") or 0,
        genre_ids=item.get("genre_ids") or [],
    )


@router.get("/search", response_model=SearchResponse)
async def search_content(
    q: Annotated[str, Query(min_length=2)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> SearchResponse:
    try:
        tmdb_response = await search_multi(q, page)
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="TMDB tardó demasiado en responder.",
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="No fue posible consultar TMDB.",
        ) from error

    results = []

    for item in tmdb_response.get("results", []):
        transformed = transform_result(item)

        if transformed is not None:
            results.append(transformed)

    return SearchResponse(
        page=tmdb_response.get("page", page),
        total_pages=tmdb_response.get("total_pages", 0),
        results=results,
    )
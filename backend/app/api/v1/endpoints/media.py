from typing import Annotated, Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Path

from app.integrations.tmdb.client import (
    get_media_details as get_tmdb_details,
)
from app.schemas.media import MediaDetails


router = APIRouter()

MediaType = Literal["movie", "tv"]

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/original"


def extract_year(date_value: Any) -> int | None:
    if not date_value:
        return None

    try:
        return int(date_value[:4])
    except (TypeError, ValueError):
        return None


def transform_media_details(
    item: dict[str, Any],
    media_type: MediaType,
) -> MediaDetails:
    if media_type == "movie":
        title = item.get("title")
        original_title = item.get("original_title")
        release_date = item.get("release_date")
        runtime = item.get("runtime")
        number_of_seasons = None
        number_of_episodes = None
    else:
        title = item.get("name")
        original_title = item.get("original_name")
        release_date = item.get("first_air_date")

        episode_runtimes = item.get("episode_run_time") or []
        runtime = episode_runtimes[0] if episode_runtimes else None

        number_of_seasons = item.get("number_of_seasons")
        number_of_episodes = item.get("number_of_episodes")

    poster_path = item.get("poster_path")
    backdrop_path = item.get("backdrop_path")

    return MediaDetails(
        tmdb_id=item["id"],
        media_type=media_type,
        title=title or "",
        original_title=original_title or "",
        overview=item.get("overview") or "",
        poster_url=(
            f"{POSTER_BASE_URL}{poster_path}"
            if poster_path
            else None
        ),
        backdrop_url=(
            f"{BACKDROP_BASE_URL}{backdrop_path}"
            if backdrop_path
            else None
        ),
        release_year=extract_year(release_date),
        rating=item.get("vote_average") or 0,
        vote_count=item.get("vote_count") or 0,
        genres=item.get("genres") or [],
        runtime=runtime,
        number_of_seasons=number_of_seasons,
        number_of_episodes=number_of_episodes,
    )


async def fetch_details(
    media_type: MediaType,
    tmdb_id: int,
) -> MediaDetails:
    try:
        tmdb_response = await get_tmdb_details(
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

    return transform_media_details(tmdb_response, media_type)


@router.get(
    "/media/movie/{tmdb_id}",
    response_model=MediaDetails,
)
async def movie_details(
    tmdb_id: Annotated[int, Path(gt=0)],
) -> MediaDetails:
    return await fetch_details("movie", tmdb_id)


@router.get(
    "/media/tv/{tmdb_id}",
    response_model=MediaDetails,
)
async def tv_details(
    tmdb_id: Annotated[int, Path(gt=0)],
) -> MediaDetails:
    return await fetch_details("tv", tmdb_id)
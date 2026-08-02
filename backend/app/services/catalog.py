from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media import Media, MediaType


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def upsert_media_from_tmdb(
    session: Session,
    item: dict[str, Any],
    media_type: MediaType,
) -> Media:
    media = session.scalar(
        select(Media).where(
            Media.tmdb_id == item["id"],
            Media.media_type == media_type,
        )
    )

    if media is None:
        media = Media(
            tmdb_id=item["id"],
            media_type=media_type,
            title="",
        )
        session.add(media)

    if media_type == MediaType.MOVIE:
        title = item.get("title")
        original_title = item.get("original_title")
        release_date = item.get("release_date")
        runtime = item.get("runtime")
    else:
        title = item.get("name")
        original_title = item.get("original_name")
        release_date = item.get("first_air_date")

        episode_runtimes = (
            item.get("episode_run_time") or []
        )
        runtime = (
            episode_runtimes[0]
            if episode_runtimes
            else None
        )

    media.title = title or ""
    media.original_title = original_title
    media.overview = item.get("overview")
    media.poster_path = item.get("poster_path")
    media.backdrop_path = item.get("backdrop_path")
    media.release_date = parse_date(release_date)
    media.tmdb_rating = (
        item.get("vote_average") or 0
    )
    media.vote_count = item.get("vote_count") or 0
    media.runtime = runtime
    media.metadata_updated_at = datetime.now(
        timezone.utc
    )

    return media
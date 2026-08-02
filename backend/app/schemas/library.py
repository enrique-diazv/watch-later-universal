from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.library import LibraryStatus
from app.models.media import MediaType


class LibraryItemCreate(BaseModel):
    tmdb_id: int = Field(gt=0)
    media_type: MediaType
    status: LibraryStatus = (
        LibraryStatus.PLAN_TO_WATCH
    )


class LibraryItemUpdate(BaseModel):
    status: LibraryStatus | None = None
    user_rating: float | None = Field(
        default=None,
        ge=0,
        le=10,
    )
    is_favorite: bool | None = None
    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


class LibraryMediaRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    tmdb_id: int
    media_type: MediaType
    title: str
    original_title: str | None
    overview: str | None
    poster_path: str | None
    backdrop_path: str | None
    release_date: date | None
    tmdb_rating: float
    vote_count: int
    runtime: int | None


class LibraryItemRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    status: LibraryStatus
    user_rating: float | None
    is_favorite: bool
    notes: str | None
    added_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    media: LibraryMediaRead
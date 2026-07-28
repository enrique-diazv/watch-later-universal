from typing import Literal

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    tmdb_id: int
    media_type: Literal["movie", "tv"]
    title: str
    overview: str = ""
    poster_url: str | None = None
    release_year: int | None = None
    rating: float = Field(default=0, ge=0, le=10)
    genre_ids: list[int] = Field(default_factory=list)


class SearchResponse(BaseModel):
    page: int
    total_pages: int
    results: list[SearchResult]
  

class Genre(BaseModel):
    id: int
    name: str


class MediaDetails(BaseModel):
    tmdb_id: int
    media_type: Literal["movie", "tv"]
    title: str
    original_title: str = ""
    overview: str = ""
    poster_url: str | None = None
    backdrop_url: str | None = None
    release_year: int | None = None
    rating: float = Field(default=0, ge=0, le=10)
    vote_count: int = Field(default=0, ge=0)
    genres: list[Genre] = Field(default_factory=list)
    runtime: int | None = Field(default=None, ge=0)
    number_of_seasons: int | None = Field(default=None, ge=0)
    number_of_episodes: int | None = Field(default=None, ge=0)

AvailabilityType = Literal[
    "flatrate",
    "free",
    "ads",
    "rent",
    "buy",
]


class WatchProvider(BaseModel):
    tmdb_provider_id: int
    name: str
    logo_url: str | None = None
    display_priority: int = Field(default=0, ge=0)
    availability_type: AvailabilityType


class WatchProvidersResponse(BaseModel):
    tmdb_id: int
    media_type: Literal["movie", "tv"]
    region: str = Field(min_length=2, max_length=2)
    link: str | None = None
    providers: list[WatchProvider] = Field(default_factory=list)
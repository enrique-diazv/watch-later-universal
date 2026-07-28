from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


FAKE_MOVIE = {
    "id": 603,
    "title": "Matrix",
    "original_title": "The Matrix",
    "overview": "Una hacker descubre la verdad.",
    "poster_path": "/matrix.jpg",
    "backdrop_path": "/matrix-backdrop.jpg",
    "release_date": "1999-03-30",
    "vote_average": 8.2,
    "vote_count": 27000,
    "genres": [
        {"id": 28, "name": "Acción"},
        {"id": 878, "name": "Ciencia ficción"},
    ],
    "runtime": 136,
}


FAKE_TV = {
    "id": 1399,
    "name": "Juego de tronos",
    "original_name": "Game of Thrones",
    "overview": "Nueve familias luchan por el poder.",
    "poster_path": "/got.jpg",
    "backdrop_path": "/got-backdrop.jpg",
    "first_air_date": "2011-04-17",
    "vote_average": 8.5,
    "vote_count": 25000,
    "genres": [
        {"id": 18, "name": "Drama"},
    ],
    "episode_run_time": [60],
    "number_of_seasons": 8,
    "number_of_episodes": 73,
}


def test_movie_details() -> None:
    mocked_details = AsyncMock(return_value=FAKE_MOVIE)

    with patch(
        "app.api.v1.endpoints.media.get_tmdb_details",
        mocked_details,
    ):
        response = client.get("/api/v1/media/movie/603")

    assert response.status_code == 200

    data = response.json()

    assert data["tmdb_id"] == 603
    assert data["media_type"] == "movie"
    assert data["title"] == "Matrix"
    assert data["release_year"] == 1999
    assert data["runtime"] == 136
    assert data["number_of_seasons"] is None

    mocked_details.assert_awaited_once_with("movie", 603)


def test_tv_details() -> None:
    mocked_details = AsyncMock(return_value=FAKE_TV)

    with patch(
        "app.api.v1.endpoints.media.get_tmdb_details",
        mocked_details,
    ):
        response = client.get("/api/v1/media/tv/1399")

    assert response.status_code == 200

    data = response.json()

    assert data["tmdb_id"] == 1399
    assert data["media_type"] == "tv"
    assert data["title"] == "Juego de tronos"
    assert data["release_year"] == 2011
    assert data["runtime"] == 60
    assert data["number_of_seasons"] == 8
    assert data["number_of_episodes"] == 73

    mocked_details.assert_awaited_once_with("tv", 1399)


def test_media_not_found() -> None:
    request = httpx.Request(
        "GET",
        "https://api.themoviedb.org/3/movie/999999999",
    )
    response_from_tmdb = httpx.Response(
        status_code=404,
        request=request,
    )
    tmdb_error = httpx.HTTPStatusError(
        "Not found",
        request=request,
        response=response_from_tmdb,
    )

    with patch(
        "app.api.v1.endpoints.media.get_tmdb_details",
        new=AsyncMock(side_effect=tmdb_error),
    ):
        response = client.get(
            "/api/v1/media/movie/999999999",
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Contenido no encontrado.",
    }
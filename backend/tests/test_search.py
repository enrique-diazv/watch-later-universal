from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


FAKE_TMDB_RESPONSE = {
    "page": 1,
    "total_pages": 1,
    "results": [
        {
            "id": 603,
            "media_type": "movie",
            "title": "Matrix",
            "overview": "Una hacker descubre la verdad.",
            "poster_path": "/matrix.jpg",
            "release_date": "1999-03-30",
            "vote_average": 8.2,
            "genre_ids": [28, 878],
        },
        {
            "id": 100,
            "media_type": "person",
            "name": "Una persona",
        },
        {
            "id": 999,
            "media_type": "tv",
            "name": "Matrix: La serie",
            "overview": "",
            "poster_path": None,
            "first_air_date": "2020-01-01",
            "vote_average": 7.5,
            "genre_ids": [10765],
        },
    ],
}


def test_search_returns_only_movies_and_tv() -> None:
    mocked_search = AsyncMock(return_value=FAKE_TMDB_RESPONSE)

    with patch(
        "app.api.v1.endpoints.search.search_multi",
        mocked_search,
    ):
        response = client.get(
            "/api/v1/search",
            params={"q": "matrix", "page": 1},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["total_pages"] == 1
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Matrix"
    assert data["results"][0]["release_year"] == 1999
    assert data["results"][1]["media_type"] == "tv"

    mocked_search.assert_awaited_once_with("matrix", 1)


def test_search_rejects_short_queries() -> None:
    response = client.get(
        "/api/v1/search",
        params={"q": "a"},
    )

    assert response.status_code == 422
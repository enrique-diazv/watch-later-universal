from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


FAKE_PROVIDERS = {
    "id": 603,
    "results": {
        "MX": {
            "link": "https://www.themoviedb.org/movie/603/watch",
            "flatrate": [
                {
                    "provider_id": 8,
                    "provider_name": "Netflix",
                    "logo_path": "/netflix.jpg",
                    "display_priority": 1,
                }
            ],
            "rent": [
                {
                    "provider_id": 2,
                    "provider_name": "Apple TV",
                    "logo_path": "/apple.jpg",
                    "display_priority": 2,
                }
            ],
            "buy": [
                {
                    "provider_id": 2,
                    "provider_name": "Apple TV",
                    "logo_path": "/apple.jpg",
                    "display_priority": 2,
                }
            ],
        },
        "US": {
            "flatrate": [
                {
                    "provider_id": 15,
                    "provider_name": "Hulu",
                    "logo_path": "/hulu.jpg",
                    "display_priority": 1,
                }
            ],
        },
    },
}


def test_providers_returns_only_configured_region() -> None:
    mocked_providers = AsyncMock(
        return_value=FAKE_PROVIDERS,
    )
    fake_settings = SimpleNamespace(tmdb_region="MX")

    with (
        patch(
            "app.api.v1.endpoints.providers.get_watch_providers",
            mocked_providers,
        ),
        patch(
            "app.api.v1.endpoints.providers.get_settings",
            return_value=fake_settings,
        ),
    ):
        response = client.get(
            "/api/v1/media/movie/603/providers",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["tmdb_id"] == 603
    assert data["media_type"] == "movie"
    assert data["region"] == "MX"
    assert len(data["providers"]) == 3

    assert data["providers"][0]["name"] == "Netflix"
    assert (
        data["providers"][0]["availability_type"]
        == "flatrate"
    )
    assert data["providers"][1]["name"] == "Apple TV"
    assert (
        data["providers"][1]["availability_type"]
        == "rent"
    )
    assert (
        data["providers"][2]["availability_type"]
        == "buy"
    )

    provider_names = [
        provider["name"]
        for provider in data["providers"]
    ]
    assert "Hulu" not in provider_names

    mocked_providers.assert_awaited_once_with(
        "movie",
        603,
    )


def test_providers_returns_empty_list_when_region_is_missing() -> None:
    mocked_providers = AsyncMock(
        return_value={
            "id": 603,
            "results": {
                "US": {},
            },
        }
    )
    fake_settings = SimpleNamespace(tmdb_region="MX")

    with (
        patch(
            "app.api.v1.endpoints.providers.get_watch_providers",
            mocked_providers,
        ),
        patch(
            "app.api.v1.endpoints.providers.get_settings",
            return_value=fake_settings,
        ),
    ):
        response = client.get(
            "/api/v1/media/movie/603/providers",
        )

    assert response.status_code == 200
    assert response.json()["region"] == "MX"
    assert response.json()["providers"] == []
    assert response.json()["link"] is None


def test_providers_rejects_invalid_media_type() -> None:
    response = client.get(
        "/api/v1/media/person/603/providers",
    )

    assert response.status_code == 422
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "watch-later-api",
    }

def test_cors_allows_local_frontend() -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )

def test_cors_allows_registration_post() -> None:
    response = client.options(
        "/api/v1/auth/register",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert "POST" in response.headers[
        "access-control-allow-methods"
    ]

def test_cors_allows_authenticated_library_requests(
) -> None:
    response = client.options(
        "/api/v1/library/example-id",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": (
                "Authorization, Content-Type"
            ),
        },
    )

    assert response.status_code == 200
    assert (
        response.headers[
            "access-control-allow-credentials"
        ]
        == "true"
    )
    assert "PATCH" in response.headers[
        "access-control-allow-methods"
    ]
    assert "authorization" in response.headers[
        "access-control-allow-headers"
    ].lower()
"""Contract tests for the service health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from healthcare_support.api.app import create_app


def test_health_returns_ok_without_session_proof() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_preflight_allows_local_frontend() -> None:
    with TestClient(create_app()) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

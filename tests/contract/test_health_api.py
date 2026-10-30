"""Contract tests for the service health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from banking_support.api.app import create_app


def test_health_returns_ok_without_session_proof() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

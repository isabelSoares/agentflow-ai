"""Shared pytest helpers for the test suite."""

from __future__ import annotations

from fastapi.testclient import TestClient


def start_session(client: TestClient) -> tuple[str, dict[str, str]]:
    """Create a conversation and return ``(conversation_id, proof_headers)``."""
    response = client.post("/conversations")
    assert response.status_code == 201, response.text
    conversation_id = response.json()["conversation_id"]
    proof = response.headers.get("X-Session-Proof")
    assert proof, "POST /conversations must return an X-Session-Proof header"
    return conversation_id, proof_headers(proof)


def proof_headers(proof: str) -> dict[str, str]:
    """Return request headers carrying the session ownership proof."""
    return {"X-Session-Proof": proof}

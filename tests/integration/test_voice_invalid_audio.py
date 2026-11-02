"""Integration tests for invalid and unintelligible audio."""

from __future__ import annotations

import io
import wave

import pytest
from fastapi.testclient import TestClient

from healthcare_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    ScriptedFakeExtractor,
)
from healthcare_support.api.app import AppState, create_app
from healthcare_support.voice.service import build_voice_service
from healthcare_support.voice.stt import FakeSTT
from healthcare_support.voice.tts import FakeTTS


def _make_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00" * 320)
    return buffer.getvalue()


@pytest.fixture
def client() -> TestClient:
    extractor = ScriptedFakeExtractor([ExtractionResult(intent=ExtractionIntent.CHITCHAT)])
    app_state = AppState()
    app_state.extractor = extractor
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.patient_repository,
        extractor,
        default_phone_region=app_state.settings.default_phone_region,
    )
    app_state.history_store = app_state.history_store.__class__(
        app_state.verification_graph,
        max_history_messages=app_state.settings.max_history_messages,
        redaction_enabled=app_state.settings.history_redaction_enabled,
    )
    app_state.voice_config = app_state.voice_config.model_copy(
        update={"enabled": True, "stt_enabled": True, "tts_enabled": True}
    )
    app_state.stt_client = FakeSTT()
    app_state.tts_client = FakeTTS(audio=b"AUDIO")
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )
    with TestClient(create_app(app_state)) as test_client:
        yield test_client


def test_unsupported_format_returns_422(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.mp3", io.BytesIO(b"not-an-audio-file"), "audio/mp3")},
        headers=headers,
    )

    assert response.status_code == 422


def test_oversized_audio_returns_422(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    # Exceed the default 1 MB limit.
    big_audio = b"\x00" * (1_048_576 + 1)
    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(big_audio), "audio/wav")},
        headers=headers,
    )

    assert response.status_code == 422


def test_silent_audio_returns_clarification(client: TestClient) -> None:
    """Audio that cannot be transcribed reliably results in a clarification
    response without invoking the healthcare workflow.
    """
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    app_state = client.app.state.app_state
    app_state.stt_client = FakeSTT(default="")
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )

    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert "repeat" in body["reply"].lower() or "catch" in body["reply"].lower()
    assert body["identified"] is False
    assert body["authenticated"] is False


def test_validation_error_does_not_expose_internals(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.mp3", io.BytesIO(b"x"), "audio/mp3")},
        headers=headers,
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "internal" not in detail.lower()
    assert "rejected_reason" not in detail.lower()

"""Privacy tests for the voice interface."""

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


def _build_app_state() -> AppState:
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name="Lisa", phone="+14155552671", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
            )
        ]
    )
    app_state = AppState()
    app_state.extractor = extractor
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.customer_repository,
        extractor,
        default_phone_region=app_state.settings.default_phone_region,
    )
    app_state.history_store = app_state.history_store.__class__(
        app_state.verification_graph,
        max_history_messages=app_state.settings.max_history_messages,
        redaction_enabled=app_state.settings.history_redaction_enabled,
    )
    app_state.voice_config = app_state.voice_config.model_copy(
        update={"enabled": True, "stt_enabled": True, "tts_enabled": False}
    )
    app_state.stt_client = FakeSTT(default="My IBAN is DE89370400440532013000")
    app_state.tts_client = FakeTTS()
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )
    return app_state


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app(_build_app_state())) as test_client:
        yield test_client


def test_voice_response_does_not_include_raw_audio(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    audio = _make_wav()
    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(audio), "audio/wav")},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert audio not in response.content
    assert body.get("audio") is None


def test_voice_response_does_not_expose_transcript(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert "DE89370400440532013000" not in body["reply"]
    assert "IBAN" not in body.get("reply", "")

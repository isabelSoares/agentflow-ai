"""Observability tests for the voice interface."""

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
        update={"enabled": True, "stt_enabled": True, "tts_enabled": False}
    )
    app_state.stt_client = FakeSTT(default="hello")
    app_state.tts_client = FakeTTS()
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )
    with TestClient(create_app(app_state)) as test_client:
        yield test_client


def test_voice_request_emits_session_and_guardrail_events(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO", logger="healthcare_support.audit")

    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
    )

    audit_messages = " ".join(
        record.getMessage()
        for record in caplog.records
        if record.name == "healthcare_support.audit"
    )
    assert "session_access_granted" in audit_messages
    assert "guardrail_allowed" in audit_messages


def test_voice_request_audit_does_not_include_raw_audio(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO", logger="healthcare_support.audit")

    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}
    audio = _make_wav()

    client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(audio), "audio/wav")},
        headers=headers,
    )

    audit_messages = " ".join(
        record.getMessage()
        for record in caplog.records
        if record.name == "healthcare_support.audit"
    )
    assert audio.hex() not in audit_messages
    assert "my date of birth" not in audit_messages.lower()

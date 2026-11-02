"""Contract tests for the voice endpoint response shape."""

from __future__ import annotations

import io
import wave

import pytest
from fastapi.testclient import TestClient

from healthcare_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from healthcare_support.api.app import AppState, create_app
from healthcare_support.data.seed import PATIENTS
from healthcare_support.domain.routing import IntentClassification, SupportIntent
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
    """Return an AppState configured with deterministic fakes for tests."""
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name=PATIENTS[0].name,
                phone=PATIENTS[0].phone,
                intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
            ),
            ExtractionResult(
                secret_answer=PATIENTS[0].secret_answer, intent=ExtractionIntent.ANSWER_SECRET
            ),
        ]
    )
    classifier = ScriptedFakeSupportIntentClassifier(
        [IntentClassification(intent=SupportIntent.GENERAL_BANKING)]
    )
    app_state = AppState()
    app_state.extractor = extractor
    app_state.intent_classifier = classifier
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.patient_repository,
        extractor,
        default_phone_region=app_state.settings.default_phone_region,
        intent_classifier=classifier,
    )
    app_state.history_store = app_state.history_store.__class__(
        app_state.verification_graph,
        max_history_messages=app_state.settings.max_history_messages,
        redaction_enabled=app_state.settings.history_redaction_enabled,
    )
    app_state.voice_config = app_state.voice_config.model_copy(
        update={"enabled": True, "stt_enabled": True, "tts_enabled": True}
    )
    app_state.stt_client = FakeSTT(default="I need help with my bank account")
    app_state.tts_client = FakeTTS(audio=b"AUDIO")
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


def test_voice_endpoint_returns_expected_shape(client: TestClient) -> None:
    start = client.post("/conversations")
    assert start.status_code == 201
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    audio = _make_wav()
    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(audio), "audio/wav")},
        headers=headers,
        data={"enable_tts": "true"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "conversation_id" in body
    assert "reply" in body
    assert "identified" in body
    assert "authenticated" in body
    assert "terminated" in body
    assert "classification" in body
    assert "routing_status" in body
    assert "routing_intent" in body
    assert "support_department" in body
    assert "audio" in body
    assert "audio_content_type" in body
    assert "audio_failed" in body
    assert body["audio"] is not None
    assert body["audio_content_type"] == "audio/wav"
    assert body["audio_failed"] is False


def test_voice_endpoint_disabled_returns_503() -> None:
    app_state = _build_app_state()
    app_state.voice_config = app_state.voice_config.model_copy(update={"enabled": False})
    with TestClient(create_app(app_state)) as disabled_client:
        start = disabled_client.post("/conversations")
        conversation_id = start.json()["conversation_id"]
        headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

        audio = _make_wav()
        response = disabled_client.post(
            f"/conversations/{conversation_id}/voice/messages",
            files={"audio": ("test.wav", io.BytesIO(audio), "audio/wav")},
            headers=headers,
        )

        assert response.status_code == 503
        assert "not enabled" in response.json()["detail"].lower()

"""Integration tests for voice-based verification."""

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
from healthcare_support.data.seed import CUSTOMERS
from healthcare_support.domain.conversation import CustomerClassification
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
    extractor = ScriptedFakeExtractor(
        [
            ExtractionResult(
                name=CUSTOMERS[0].name,
                phone=CUSTOMERS[0].phone,
                intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
            ),
            ExtractionResult(
                secret_answer=CUSTOMERS[0].secret_answer, intent=ExtractionIntent.ANSWER_SECRET
            ),
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
    app_state.stt_client = FakeSTT(default="My name is Lisa")
    app_state.tts_client = FakeTTS()
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )
    with TestClient(create_app(app_state)) as test_client:
        yield test_client


def test_voice_verification_does_not_auto_authenticate(client: TestClient) -> None:
    """Spoken verification details are transcribed and passed to the Greeter,
    but the transcription alone does not authenticate the customer.
    """
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
    assert body["identified"] is True
    assert body["authenticated"] is False
    assert "security question" in body["reply"].lower()


def test_voice_verification_advances_after_secret_answer(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
    )

    app_state = client.app.state.app_state
    app_state.stt_client = FakeSTT(default="Yoda")
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
    assert body["authenticated"] is True
    expected_classification = (
        CustomerClassification.PREMIUM.value
        if CUSTOMERS[0].is_premium
        else CustomerClassification.REGULAR.value
    )
    assert body["classification"] == expected_classification

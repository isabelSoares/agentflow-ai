"""Integration tests for voice messages."""

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
from healthcare_support.data.seed import CUSTOMERS
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


def _build_app_state(default_text: str = "I need help with my bank account") -> AppState:
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
    classifier = ScriptedFakeSupportIntentClassifier(
        [IntentClassification(intent=SupportIntent.GENERAL_BANKING)]
    )
    app_state = AppState()
    app_state.extractor = extractor
    app_state.intent_classifier = classifier
    from healthcare_support.agents.graph import build_verification_graph

    app_state.verification_graph = build_verification_graph(
        app_state.customer_repository,
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
    app_state.stt_client = FakeSTT(default=default_text)
    app_state.tts_client = FakeTTS(audio=b"AUDIO", fail=False)
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


def test_spoken_banking_request_returns_text_and_audio(client: TestClient) -> None:
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
        data={"enable_tts": "true"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"]
    assert body["audio"] is not None
    assert body["audio_content_type"] == "audio/wav"
    assert body["audio_failed"] is False


def test_spoken_request_matches_text_endpoint_response() -> None:
    # Use separate app states so the scripted extractor starts from the same
    # position for both the voice and text requests.
    with (
        TestClient(
            create_app(_build_app_state(default_text="I need help with my bank account"))
        ) as voice_client,
        TestClient(
            create_app(_build_app_state(default_text="I need help with my bank account"))
        ) as text_client,
    ):
        voice_start = voice_client.post("/conversations")
        voice_id = voice_start.json()["conversation_id"]
        voice_headers = {"X-Session-Proof": voice_start.headers["X-Session-Proof"]}
        voice_response = voice_client.post(
            f"/conversations/{voice_id}/voice/messages",
            files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
            headers=voice_headers,
            data={"enable_tts": "false"},
        )

        text_start = text_client.post("/conversations")
        text_id = text_start.json()["conversation_id"]
        text_headers = {"X-Session-Proof": text_start.headers["X-Session-Proof"]}
        text_response = text_client.post(
            f"/conversations/{text_id}/messages",
            json={"text": "I need help with my bank account"},
            headers=text_headers,
        )

        assert voice_response.status_code == 200
        assert text_response.status_code == 200
        voice_body = voice_response.json()
        text_body = text_response.json()
        assert voice_body["reply"] == text_body["reply"]
        assert voice_body["identified"] == text_body["identified"]
        assert voice_body["authenticated"] == text_body["authenticated"]

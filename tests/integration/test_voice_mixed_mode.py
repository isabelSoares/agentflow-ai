"""Integration tests for mixed text and voice conversations."""

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
            ExtractionResult(intent=ExtractionIntent.CHITCHAT),
        ]
    )
    classifier = ScriptedFakeSupportIntentClassifier(
        [
            IntentClassification(
                intent=SupportIntent.INSURANCE,
                needs_clarification=True,
                clarification_prompt="What type of insurance?",
            ),
            IntentClassification(
                intent=SupportIntent.YACHT_INSURANCE,
                needs_clarification=False,
            ),
        ]
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
        update={"enabled": True, "stt_enabled": True, "tts_enabled": False}
    )
    app_state.stt_client = FakeSTT(default="For a private yacht")
    app_state.tts_client = FakeTTS()
    app_state.voice_service = build_voice_service(
        config=app_state.voice_config,
        stt_client=app_state.stt_client,
        tts_client=app_state.tts_client,
        app_state=app_state,
    )
    with TestClient(create_app(app_state)) as test_client:
        yield test_client


def test_mixed_text_and_voice_preserves_context(client: TestClient) -> None:
    """A customer starts by text, continues by voice, and the assistant uses
    the ongoing conversation context to interpret the follow-up.
    """
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    # Authenticate via text.
    client.post(
        f"/conversations/{conversation_id}/messages",
        json={"text": f"I am {CUSTOMERS[0].name}, phone {CUSTOMERS[0].phone}"},
        headers=headers,
    )
    client.post(
        f"/conversations/{conversation_id}/messages",
        json={"text": CUSTOMERS[0].secret_answer},
        headers=headers,
    )

    # Ask about insurance via text; the scripted classifier requests clarification.
    r1 = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"text": "I need insurance"},
        headers=headers,
    )
    assert "type of insurance" in r1.json()["reply"].lower()

    # Continue with a short contextual voice reply.
    r2 = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
    )
    body = r2.json()
    assert body["routing_intent"] == SupportIntent.YACHT_INSURANCE.value
    assert body["authenticated"] is True


def test_verified_customer_switching_to_voice_is_not_reasked(client: TestClient) -> None:
    """After authentication, switching to voice should not restart verification."""
    start = client.post("/conversations")
    conversation_id = start.json()["conversation_id"]
    headers = {"X-Session-Proof": start.headers["X-Session-Proof"]}

    client.post(
        f"/conversations/{conversation_id}/messages",
        json={"text": f"I am {CUSTOMERS[0].name}, phone {CUSTOMERS[0].phone}"},
        headers=headers,
    )
    client.post(
        f"/conversations/{conversation_id}/messages",
        json={"text": CUSTOMERS[0].secret_answer},
        headers=headers,
    )

    response = client.post(
        f"/conversations/{conversation_id}/voice/messages",
        files={"audio": ("test.wav", io.BytesIO(_make_wav()), "audio/wav")},
        headers=headers,
    )
    body = response.json()
    assert body["authenticated"] is True
    assert "security question" not in body["reply"].lower()

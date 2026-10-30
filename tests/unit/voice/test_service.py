"""Unit tests for the voice service."""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

import pytest

from banking_support.domain.conversation import ConversationStatus
from banking_support.voice.schemas import VoiceConfig, VoiceRequest
from banking_support.voice.service import VoiceService
from banking_support.voice.stt import FakeSTT
from banking_support.voice.tts import FakeTTS
from banking_support.voice.validation import AudioValidator


def _make_invoker(
    reply: str = "Hello", status: str = ConversationStatus.COLLECTING.value
) -> Callable[[str, str, str | None], dict[str, Any]]:
    def _invoke(conversation_id: str, text: str, proof: str | None) -> dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "reply": reply,
            "status": status,
            "identified": False,
            "authenticated": False,
            "terminated": False,
            "customer_classification": None,
            "routing_status": None,
            "support_intent": None,
            "support_department": None,
            "guardrail_decision": {"outcome": "allowed"},
        }

    return _invoke


@pytest.fixture
def config() -> VoiceConfig:
    return VoiceConfig(
        enabled=True,
        stt_enabled=True,
        tts_enabled=True,
        max_audio_bytes=1_000_000,
        max_audio_seconds=60,
        supported_input_types=frozenset({"audio/wav", "audio/webm"}),
        output_content_type="audio/wav",
    )


@pytest.fixture
def service(config: VoiceConfig) -> VoiceService:
    return VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=FakeSTT(default="I need help"),
        tts_client=FakeTTS(audio=b"AUDIO"),
        graph_invoker=_make_invoker(),
    )


def _audio_bytes() -> bytes:
    return b"valid-audio"


def test_voice_service_happy_path(service: VoiceService) -> None:
    request = VoiceRequest(
        conversation_id="conv-1",
        content_type="audio/wav",
        enable_tts=True,
    )
    response = service.handle_voice_request(request, _audio_bytes())

    assert response["conversation_id"] == "conv-1"
    assert response["reply"] == "Hello"
    assert response["authenticated"] is False
    assert response["audio_failed"] is False
    assert response["audio"] == base64.b64encode(b"AUDIO").decode("ascii")
    assert response["audio_content_type"] == "audio/wav"


def test_voice_service_tts_disabled(service: VoiceService) -> None:
    request = VoiceRequest(
        conversation_id="conv-1",
        content_type="audio/wav",
        enable_tts=False,
    )
    response = service.handle_voice_request(request, _audio_bytes())

    assert response["reply"] == "Hello"
    assert response["audio"] is None
    assert response["audio_failed"] is False


def test_voice_service_tts_failure(config: VoiceConfig) -> None:
    service = VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=FakeSTT(default="I need help"),
        tts_client=FakeTTS(fail=True),
        graph_invoker=_make_invoker(),
    )
    request = VoiceRequest(
        conversation_id="conv-1",
        content_type="audio/wav",
        enable_tts=True,
    )
    response = service.handle_voice_request(request, _audio_bytes())

    assert response["reply"] == "Hello"
    assert response["audio"] is None
    assert response["audio_failed"] is True


def test_voice_service_passes_transcribed_text_to_graph(config: VoiceConfig) -> None:
    captured: dict[str, str] = {}

    def _capture(conversation_id: str, text: str, proof: str | None) -> dict[str, Any]:
        captured["conversation_id"] = conversation_id
        captured["text"] = text
        return {
            "conversation_id": conversation_id,
            "reply": "Got it",
            "status": ConversationStatus.COLLECTING.value,
            "identified": False,
            "authenticated": False,
            "terminated": False,
            "customer_classification": None,
            "routing_status": None,
            "support_intent": None,
            "support_department": None,
            "guardrail_decision": {"outcome": "allowed"},
        }

    service = VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=FakeSTT(default="My spoken words"),
        tts_client=FakeTTS(),
        graph_invoker=_capture,
    )
    request = VoiceRequest(
        conversation_id="conv-2",
        content_type="audio/wav",
        enable_tts=False,
    )
    service.handle_voice_request(request, _audio_bytes())

    assert captured["conversation_id"] == "conv-2"
    assert captured["text"] == "My spoken words"


def test_voice_service_uses_conversation_id_for_graph_invocation(config: VoiceConfig) -> None:
    captured_id: str | None = None

    def _capture_id(conversation_id: str, text: str, proof: str | None) -> dict[str, Any]:
        nonlocal captured_id
        captured_id = conversation_id
        return {
            "conversation_id": conversation_id,
            "reply": "OK",
            "status": ConversationStatus.COLLECTING.value,
            "identified": False,
            "authenticated": False,
            "terminated": False,
            "customer_classification": None,
            "routing_status": None,
            "support_intent": None,
            "support_department": None,
            "guardrail_decision": {"outcome": "allowed"},
        }

    service = VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=FakeSTT(),
        tts_client=FakeTTS(),
        graph_invoker=_capture_id,
    )
    request = VoiceRequest(
        conversation_id="mixed-session-123",
        content_type="audio/wav",
        enable_tts=False,
    )
    service.handle_voice_request(request, _audio_bytes())

    assert captured_id == "mixed-session-123"


def test_voice_service_skips_tts_for_blocked_guardrail(config: VoiceConfig) -> None:
    def _block(conversation_id: str, text: str, proof: str | None) -> dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "reply": "I cannot help with that.",
            "status": ConversationStatus.COLLECTING.value,
            "identified": False,
            "authenticated": False,
            "terminated": False,
            "customer_classification": None,
            "routing_status": None,
            "support_intent": None,
            "support_department": None,
            "guardrail_decision": {
                "outcome": "blocked",
                "reason_category": "prohibited_financial_action",
            },
        }

    service = VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=FakeSTT(),
        tts_client=FakeTTS(audio=b"SHOULD_NOT_BE_RETURNED"),
        graph_invoker=_block,
    )
    request = VoiceRequest(
        conversation_id="conv-1",
        content_type="audio/wav",
        enable_tts=True,
    )
    response = service.handle_voice_request(request, _audio_bytes())

    assert response["reply"] == "I cannot help with that."
    assert response["audio"] is None
    assert response["audio_failed"] is False


def test_voice_service_low_confidence_returns_clarification(config: VoiceConfig) -> None:
    class _UnreliableSTT:
        def transcribe(self, audio: bytes, content_type: str) -> Any:
            from banking_support.voice.schemas import TranscriptionResult

            return TranscriptionResult(
                text="",
                is_reliable=False,
                fallback_message="Please repeat that.",
            )

    service = VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=_UnreliableSTT(),
        tts_client=FakeTTS(),
        graph_invoker=_make_invoker(),
    )
    request = VoiceRequest(
        conversation_id="conv-1",
        content_type="audio/wav",
        enable_tts=True,
    )
    response = service.handle_voice_request(request, _audio_bytes())

    assert response["reply"] == "Please repeat that."
    assert response["audio"] is None
    assert response["audio_failed"] is False
    assert response["identified"] is False
    assert response["authenticated"] is False

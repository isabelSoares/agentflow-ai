"""Voice service orchestrating audio validation, STT, graph invocation, and TTS."""

from __future__ import annotations

import base64
import logging
from collections.abc import Callable
from typing import Any, cast

from healthcare_support.domain.conversation import ConversationStatus
from healthcare_support.voice.schemas import (
    VoiceConfig,
    VoiceRequest,
)
from healthcare_support.voice.stt import STTClient
from healthcare_support.voice.tts import TTSClient
from healthcare_support.voice.validation import AudioValidator

logger = logging.getLogger(__name__)

CLARIFICATION_MESSAGE = "I'm sorry, I didn't catch that. Could you please repeat?"


class VoiceService:
    """Orchestrate a single voice turn without duplicating banking logic.

    The voice layer treats audio and its transcription as untrusted customer
    input. It never makes authentication or authorization decisions; those
    remain the responsibility of the existing deterministic workflow.
    """

    def __init__(
        self,
        *,
        config: VoiceConfig,
        validator: AudioValidator,
        stt_client: STTClient,
        tts_client: TTSClient,
        graph_invoker: Callable[[str, str, str | None], dict[str, Any]],
    ) -> None:
        self._config = config
        self._validator = validator
        self._stt = stt_client
        self._tts = tts_client
        self._graph_invoker = graph_invoker

    def handle_voice_request(
        self,
        request: VoiceRequest,
        audio: bytes,
        presented_proof: str | None = None,
    ) -> dict[str, Any]:
        """Process a voice request and return a response dictionary.

        The audio recording and its transcription are treated as untrusted
        customer input. They are never used as proof of identity or authority;
        authentication and authorization decisions remain the responsibility of
        the existing deterministic workflow.

        The returned dictionary contains the same fields as the existing text
        ``ConversationTurnResponse`` plus optional speech-related fields. It can
        be passed directly to ``VoiceTurnResponse``.
        """
        validation = self._validator.validate(audio, request.content_type)
        if not validation.is_valid:
            return self._build_response(
                request,
                reply=validation.customer_message or CLARIFICATION_MESSAGE,
            )

        transcription = self._stt.transcribe(audio, request.content_type)
        if not transcription.is_reliable:
            return self._build_response(
                request,
                reply=transcription.fallback_message or CLARIFICATION_MESSAGE,
            )

        result = self._graph_invoker(request.conversation_id, transcription.text, presented_proof)
        reply = result.get("reply") or ""

        audio_bytes: bytes | None = None
        audio_content_type: str | None = None
        audio_failed = False

        enable_tts = request.enable_tts and self._config.tts_enabled
        if enable_tts and reply and self._is_safe_to_speak(result):
            speech = self._tts.synthesize(reply, self._config.output_content_type)
            if speech.failed:
                audio_failed = True
            else:
                audio_bytes = speech.audio
                audio_content_type = speech.content_type

        status = result.get("status")
        return self._build_response(
            request,
            reply=reply,
            identified=status
            in (ConversationStatus.IDENTIFIED.value, ConversationStatus.AUTHENTICATED.value),
            authenticated=status == ConversationStatus.AUTHENTICATED.value,
            terminated=bool(result.get("terminated")),
            classification=result.get("customer_classification"),
            routing_status=result.get("routing_status"),
            routing_intent=result.get("support_intent"),
            support_department=result.get("support_department"),
            audio=audio_bytes,
            audio_content_type=audio_content_type,
            audio_failed=audio_failed,
        )

    @staticmethod
    def _is_safe_to_speak(result: dict[str, Any]) -> bool:
        """Return True when the assistant reply is allowed to be spoken.

        Blocked or failed guardrail outcomes are replaced with safe replies that
        must not be converted into speech, per the safe-speech requirement.
        """
        decision = result.get("guardrail_decision")
        if not isinstance(decision, dict):
            return True
        outcome = decision.get("outcome")
        return outcome == "allowed"

    @staticmethod
    def _build_response(
        request: VoiceRequest,
        *,
        reply: str,
        identified: bool = False,
        authenticated: bool = False,
        terminated: bool = False,
        classification: str | None = None,
        routing_status: str | None = None,
        routing_intent: str | None = None,
        support_department: str | None = None,
        audio: bytes | None = None,
        audio_content_type: str | None = None,
        audio_failed: bool = False,
    ) -> dict[str, Any]:
        response: dict[str, Any] = {
            "conversation_id": request.conversation_id,
            "reply": reply,
            "identified": identified,
            "authenticated": authenticated,
            "terminated": terminated,
            "classification": classification,
            "routing_status": routing_status,
            "routing_intent": routing_intent,
            "support_department": support_department,
            "audio": base64.b64encode(audio).decode("ascii") if audio else None,
            "audio_content_type": audio_content_type,
            "audio_failed": audio_failed,
        }
        return response


def build_voice_service(
    *,
    config: VoiceConfig,
    stt_client: STTClient,
    tts_client: TTSClient,
    app_state: Any,
) -> VoiceService:
    """Factory that wires the voice service to the existing graph invoker."""
    # Lazy import to avoid a circular dependency between the voice package and
    # the API invocation layer.
    from healthcare_support.api.invoker import invoke_graph

    return VoiceService(
        config=config,
        validator=AudioValidator(config),
        stt_client=stt_client,
        tts_client=tts_client,
        graph_invoker=lambda conversation_id, text, proof: cast(
            dict[str, Any], invoke_graph(app_state, conversation_id, text, proof)
        ),
    )


__all__ = ["VoiceService", "build_voice_service", "CLARIFICATION_MESSAGE"]

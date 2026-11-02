"""Speech-to-text adapters."""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from openai import OpenAI

from healthcare_support.resilience.policy import ExternalCallPolicy, call_with_policy
from healthcare_support.voice.schemas import TranscriptionResult

logger = logging.getLogger(__name__)


@runtime_checkable
class STTClient(Protocol):
    """Protocol for speech-to-text adapters."""

    def transcribe(self, audio: bytes, content_type: str) -> TranscriptionResult:
        """Transcribe the supplied audio payload."""
        ...


class OpenAISpeechToText:
    """OpenAI Whisper adapter for speech-to-text."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "whisper-1",
        base_url: str | None = None,
        policy: ExternalCallPolicy | None = None,
    ) -> None:
        self._model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._policy = policy or ExternalCallPolicy()

    def transcribe(self, audio: bytes, content_type: str) -> TranscriptionResult:
        """Transcribe audio using the OpenAI Whisper API."""
        # Whisper accepts many formats; map common content types to a file suffix.
        suffix = ".webm" if "webm" in content_type else ".wav"
        try:
            response = call_with_policy(
                lambda: self._client.audio.transcriptions.create(
                    model=self._model,
                    file=(f"audio{suffix}", audio),
                ),
                self._policy,
                fallback=None,
            )
            if response is None:
                raise TimeoutError("STT provider deadline exceeded")
            text = response.text.strip()
            # Whisper does not expose a per-request confidence score; treat any
            # non-empty result as reliable. Empty results are handled below.
            if not text:
                return TranscriptionResult(
                    text="",
                    is_reliable=False,
                    fallback_message="I'm sorry, I didn't catch that. Could you please repeat?",
                )
            return TranscriptionResult(text=text, is_reliable=True)
        except Exception:
            logger.exception("OpenAI STT transcription failed")
            return TranscriptionResult(
                text="",
                is_reliable=False,
                fallback_message="I'm sorry, I couldn't understand the audio. Please try again.",
            )


class FakeSTT:
    """Deterministic fake STT adapter for tests and local development."""

    def __init__(
        self,
        transcriptions: dict[bytes, str] | None = None,
        default: str = "I need help with an appointment",
    ) -> None:
        self._transcriptions = transcriptions or {}
        self._default = default

    def transcribe(self, audio: bytes, content_type: str) -> TranscriptionResult:
        """Return a deterministic transcription based on the audio payload."""
        text = self._transcriptions.get(audio, self._default)
        return TranscriptionResult(text=text, is_reliable=True)

    def with_mapping(self, audio: bytes, text: str) -> FakeSTT:
        """Return a new FakeSTT with an additional deterministic mapping."""
        new_mappings = dict(self._transcriptions)
        new_mappings[audio] = text
        return FakeSTT(transcriptions=new_mappings, default=self._default)

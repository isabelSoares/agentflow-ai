"""Text-to-speech adapters."""

from __future__ import annotations

import logging
from typing import Literal, Protocol, runtime_checkable

from openai import OpenAI

from banking_support.resilience.policy import ExternalCallPolicy, call_with_policy
from banking_support.voice.schemas import SpeechResult

logger = logging.getLogger(__name__)


@runtime_checkable
class TTSClient(Protocol):
    """Protocol for text-to-speech adapters."""

    def synthesize(self, text: str, content_type: str) -> SpeechResult:
        """Synthesize the supplied text into spoken audio."""
        ...


class OpenAITextToSpeech:
    """OpenAI TTS adapter for text-to-speech."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "tts-1",
        voice: str = "alloy",
        base_url: str | None = None,
        output_content_type: str = "audio/wav",
        policy: ExternalCallPolicy | None = None,
    ) -> None:
        self._model = model
        self._voice = voice
        self._output_content_type = output_content_type
        self._response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = (
            "wav" if "wav" in output_content_type else "mp3"
        )
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        # Synthesis is not assumed idempotent, so it never retries automatically.
        self._policy = ExternalCallPolicy(
            timeout_seconds=(policy.timeout_seconds if policy else 10.0),
            max_retries=0,
            backoff_seconds=(policy.backoff_seconds if policy else 0.1),
            idempotent=False,
        )

    def synthesize(self, text: str, content_type: str) -> SpeechResult:
        """Synthesize text using the OpenAI TTS API."""
        try:
            response = call_with_policy(
                lambda: self._client.audio.speech.create(
                    model=self._model,
                    voice=self._voice,
                    input=text,
                    response_format=self._response_format,
                ),
                self._policy,
                fallback=None,
            )
            if response is None:
                raise TimeoutError("TTS provider deadline exceeded")
            return SpeechResult(
                audio=response.content,
                content_type=self._output_content_type,
            )
        except Exception:
            logger.exception("OpenAI TTS synthesis failed")
            return SpeechResult(
                failed=True,
                customer_message="Speech generation is unavailable. The text response is still available.",
            )


class FakeTTS:
    """Deterministic fake TTS adapter for tests and local development."""

    def __init__(
        self,
        audio: bytes = b"FAKE_AUDIO",
        content_type: str = "audio/wav",
        fail: bool = False,
    ) -> None:
        self._audio = audio
        self._content_type = content_type
        self._fail = fail

    def synthesize(self, text: str, content_type: str) -> SpeechResult:
        """Return deterministic audio bytes or a failure result."""
        if self._fail:
            return SpeechResult(
                failed=True,
                customer_message="Speech generation failed.",
            )
        return SpeechResult(audio=self._audio, content_type=self._content_type)

"""Audio input validation for voice requests."""

from __future__ import annotations

import io
import logging
import struct
import wave
from dataclasses import dataclass

from healthcare_support.voice.schemas import VoiceConfig

logger = logging.getLogger(__name__)

# Rough heuristic for WebM/Opus mono voice: ~24 kbps = 3 KB/s.
_WEBM_BYTES_PER_SECOND_HEURISTIC = 3_000


@dataclass(frozen=True)
class AudioValidationResult:
    """Result of validating a raw audio payload."""

    is_valid: bool
    rejected_reason: str | None = None
    patient_message: str | None = None


class AudioValidationError(Exception):
    """Raised when an audio payload fails validation.

    The message is safe to expose to API consumers.
    """

    def __init__(self, reason: str, patient_message: str) -> None:
        self.reason = reason
        self.patient_message = patient_message
        super().__init__(patient_message)


class AudioValidator:
    """Validate uploaded audio against configured format, size, and duration limits."""

    def __init__(self, config: VoiceConfig) -> None:
        self._config = config

    def validate_or_raise(self, audio: bytes, content_type: str) -> None:
        """Validate audio and raise ``AudioValidationError`` if invalid."""
        result = self.validate(audio, content_type)
        if not result.is_valid:
            raise AudioValidationError(
                reason=result.rejected_reason or "invalid_audio",
                patient_message=result.patient_message or "The audio could not be processed.",
            )

    def validate(self, audio: bytes, content_type: str) -> AudioValidationResult:
        """Return a validation result for the supplied audio payload."""
        if not audio:
            return AudioValidationResult(
                is_valid=False,
                rejected_reason="empty_audio",
                patient_message="The audio file appears to be empty. Please try again.",
            )

        if content_type not in self._config.supported_input_types:
            return AudioValidationResult(
                is_valid=False,
                rejected_reason="unsupported_format",
                patient_message="The audio format is not supported. Please use a supported format.",
            )

        if len(audio) > self._config.max_audio_bytes:
            return AudioValidationResult(
                is_valid=False,
                rejected_reason="file_too_large",
                patient_message="The audio file is too large. Please send a shorter recording.",
            )

        duration = self._estimate_duration(audio, content_type)
        if duration is not None and duration > self._config.max_audio_seconds:
            return AudioValidationResult(
                is_valid=False,
                rejected_reason="duration_too_long",
                patient_message="The audio recording is too long. Please send a shorter message.",
            )

        return AudioValidationResult(is_valid=True)

    def _estimate_duration(self, audio: bytes, content_type: str) -> float | None:
        """Estimate audio duration in seconds, returning None when unknown."""
        if content_type == "audio/wav":
            return self._wav_duration(audio)
        if content_type == "audio/webm":
            return self._webm_duration_heuristic(audio)
        return None

    @staticmethod
    def _wav_duration(audio: bytes) -> float | None:
        """Compute WAV duration from the RIFF header, returning None if parsing fails."""
        try:
            with wave.open(io.BytesIO(audio), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                if rate == 0:
                    return None
                return frames / rate
        except (wave.Error, EOFError, struct.error):
            logger.debug("Failed to parse WAV header for duration estimation")
            return None

    @staticmethod
    def _webm_duration_heuristic(audio: bytes) -> float | None:
        """Estimate WebM/Opus duration using a size-based heuristic."""
        if _WEBM_BYTES_PER_SECOND_HEURISTIC == 0:
            return None
        return len(audio) / _WEBM_BYTES_PER_SECOND_HEURISTIC

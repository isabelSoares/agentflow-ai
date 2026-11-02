"""Unit tests for audio validation."""

from __future__ import annotations

import io
import wave

import pytest

from healthcare_support.voice.schemas import VoiceConfig
from healthcare_support.voice.validation import AudioValidator


def _make_wav(duration_seconds: float) -> bytes:
    """Generate a minimal WAV file of the requested duration."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        frames = int(16_000 * duration_seconds)
        wav.writeframes(b"\x00" * (frames * 2))
    return buffer.getvalue()


@pytest.fixture
def config() -> VoiceConfig:
    return VoiceConfig(
        enabled=True,
        stt_enabled=True,
        tts_enabled=True,
        max_audio_bytes=2_000_000,
        max_audio_seconds=10,
        supported_input_types=frozenset({"audio/wav", "audio/webm"}),
        output_content_type="audio/wav",
    )


@pytest.fixture
def validator(config: VoiceConfig) -> AudioValidator:
    return AudioValidator(config)


def test_valid_wav_passes(validator: AudioValidator) -> None:
    audio = _make_wav(1.0)
    result = validator.validate(audio, "audio/wav")
    assert result.is_valid is True
    assert result.rejected_reason is None


def test_empty_audio_rejected(validator: AudioValidator) -> None:
    result = validator.validate(b"", "audio/wav")
    assert result.is_valid is False
    assert result.rejected_reason == "empty_audio"
    assert result.patient_message is not None


def test_unsupported_format_rejected(validator: AudioValidator) -> None:
    audio = _make_wav(1.0)
    result = validator.validate(audio, "audio/mp3")
    assert result.is_valid is False
    assert result.rejected_reason == "unsupported_format"


def test_oversized_file_rejected(validator: AudioValidator) -> None:
    audio = b"\x00" * (validator._config.max_audio_bytes + 1)
    result = validator.validate(audio, "audio/webm")
    assert result.is_valid is False
    assert result.rejected_reason == "file_too_large"


def test_too_long_wav_rejected(validator: AudioValidator) -> None:
    audio = _make_wav(20.0)
    result = validator.validate(audio, "audio/wav")
    assert result.is_valid is False
    assert result.rejected_reason == "duration_too_long"


def test_patient_message_does_not_expose_internals(validator: AudioValidator) -> None:
    result = validator.validate(b"", "audio/wav")
    assert result.patient_message is not None
    assert "rejected_reason" not in result.patient_message.lower()
    assert "internal" not in result.patient_message.lower()

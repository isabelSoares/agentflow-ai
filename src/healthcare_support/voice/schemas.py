"""Pydantic schemas for the voice interface."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class VoiceRequest(BaseModel):
    """A patient's spoken input and its associated metadata.

    The raw audio bytes are intentionally not stored in this model; they are
    handled as untrusted binary input by the API layer and passed directly to
    the validator and speech-to-text adapter.
    """

    model_config = ConfigDict(frozen=True)

    conversation_id: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    enable_tts: bool = False


class TranscriptionResult(BaseModel):
    """Output of a speech-to-text adapter."""

    model_config = ConfigDict(frozen=True)

    text: str = ""
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_reliable: bool = False
    fallback_message: str | None = None


class SpeechResult(BaseModel):
    """Output of a text-to-speech adapter."""

    model_config = ConfigDict(frozen=True)

    audio: bytes | None = None
    content_type: str | None = None
    failed: bool = False
    patient_message: str | None = None


class VoiceConfig(BaseModel):
    """Runtime configuration for voice capabilities."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    stt_enabled: bool = False
    tts_enabled: bool = False
    max_audio_bytes: int = Field(default=1_048_576, ge=1)
    max_audio_seconds: int = Field(default=60, ge=1)
    supported_input_types: frozenset[str] = frozenset({"audio/wav", "audio/webm"})
    output_content_type: str = "audio/wav"

    @classmethod
    def from_settings(cls, settings: object) -> VoiceConfig:
        """Build a frozen voice config from application settings.

        The ``settings`` object is typed as ``object`` to avoid a circular
        dependency on the config module; callers pass the project's ``Settings``
        instance.
        """
        return cls(
            enabled=bool(getattr(settings, "voice_enabled", False)),
            stt_enabled=bool(getattr(settings, "voice_stt_enabled", False)),
            tts_enabled=bool(getattr(settings, "voice_tts_enabled", False)),
            max_audio_bytes=int(getattr(settings, "voice_max_audio_bytes", 1_048_576)),
            max_audio_seconds=int(getattr(settings, "voice_max_audio_seconds", 60)),
            supported_input_types=frozenset(
                getattr(settings, "voice_supported_input_types", {"audio/wav", "audio/webm"})
            ),
            output_content_type=str(getattr(settings, "voice_output_content_type", "audio/wav")),
        )

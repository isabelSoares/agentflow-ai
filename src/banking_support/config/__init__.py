"""Typed, environment-based configuration."""

from __future__ import annotations

import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_string_set(value: object) -> object:
    """Accept a JSON list or a comma-separated environment value."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return frozenset()
    if text.startswith("["):
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("expected a JSON list or a comma-separated string")
        return frozenset(str(item) for item in parsed)
    return frozenset(part.strip() for part in text.split(",") if part.strip())


class Settings(BaseSettings):
    """Settings are loaded from environment variables and an optional `.env` file.

    Secrets live only in the environment / `.env`; this file contains defaults and
    types.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    llm_model: str = "openai/gpt-oss-20b"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_temperature: float = 0.0
    provider_timeout_seconds: float = 10.0
    provider_max_retries: int = 1
    provider_retry_backoff_seconds: float = 0.1
    default_phone_region: str = "DE"
    log_level: str = "INFO"

    # Browser origins allowed to call the API directly. The Vite dev server
    # proxies requests, so these are only needed for direct cross-origin use.
    cors_allowed_origins: frozenset[str] = frozenset(
        {"http://localhost:5173", "http://127.0.0.1:5173"}
    )

    # Conversation history settings.
    max_history_messages: int = 20
    history_redaction_enabled: bool = True

    # Voice interface settings.
    voice_enabled: bool = False
    voice_stt_enabled: bool = False
    voice_tts_enabled: bool = False
    voice_max_audio_bytes: int = 1_048_576  # 1 MB
    voice_max_audio_seconds: int = 60
    voice_supported_input_types: frozenset[str] = frozenset({"audio/wav", "audio/webm"})
    voice_output_content_type: str = "audio/wav"
    voice_stt_model: str = "whisper-1"
    voice_tts_model: str = "tts-1"
    voice_tts_voice: str = "alloy"

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def _empty_api_key_to_none(cls, value: object) -> object:
        """Treat an empty or whitespace-only key as unconfigured."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("voice_supported_input_types", "cors_allowed_origins", mode="before")
    @classmethod
    def _parse_string_sets(cls, value: object) -> object:
        """Accept JSON lists or comma-separated environment values."""
        return _parse_string_set(value)


__all__ = ["Settings"]

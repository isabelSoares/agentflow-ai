"""Unit tests for text-to-speech adapters."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from healthcare_support.voice.tts import FakeTTS, OpenAITextToSpeech


def test_fake_tts_returns_audio() -> None:
    client = FakeTTS(audio=b"SPEECH", content_type="audio/wav")
    result = client.synthesize("hello", "audio/wav")
    assert result.audio == b"SPEECH"
    assert result.content_type == "audio/wav"
    assert result.failed is False


def test_fake_tts_can_fail() -> None:
    client = FakeTTS(fail=True)
    result = client.synthesize("hello", "audio/wav")
    assert result.failed is True
    assert result.audio is None
    assert result.customer_message is not None


def test_fake_tts_is_deterministic() -> None:
    client = FakeTTS(audio=b"X")
    first = client.synthesize("hi", "audio/wav")
    second = client.synthesize("hi", "audio/wav")
    assert first.audio == second.audio
    assert first.failed == second.failed


def test_openai_tts_returns_audio() -> None:
    mock_response = MagicMock()
    mock_response.content = b"GENERATED_AUDIO"
    mock_client = MagicMock()
    mock_client.audio.speech.create.return_value = mock_response

    client = OpenAITextToSpeech(api_key="test-key")
    client._client = mock_client
    result = client.synthesize("hello", "audio/wav")

    assert result.audio == b"GENERATED_AUDIO"
    assert result.content_type == "audio/wav"
    assert result.failed is False


def test_openai_tts_returns_failure_on_api_error() -> None:
    mock_client = MagicMock()
    mock_client.audio.speech.create.side_effect = RuntimeError("API down")

    client = OpenAITextToSpeech(api_key="test-key")
    client._client = mock_client
    result = client.synthesize("hello", "audio/wav")

    assert result.failed is True
    assert result.audio is None
    assert result.customer_message is not None


@pytest.mark.live_speech
@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="GROQ_API_KEY is not configured")
def test_openai_tts_handles_invalid_api_key() -> None:
    client = OpenAITextToSpeech(api_key="invalid-key-for-testing")
    result = client.synthesize("hello", "audio/wav")
    assert result.failed is True
    assert result.audio is None
    assert result.customer_message is not None

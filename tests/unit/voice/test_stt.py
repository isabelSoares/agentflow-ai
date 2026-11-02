"""Unit tests for speech-to-text adapters."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from healthcare_support.voice.stt import FakeSTT, OpenAISpeechToText


def test_fake_stt_returns_default_transcription() -> None:
    client = FakeSTT(default="hello world")
    result = client.transcribe(b"any", "audio/wav")
    assert result.text == "hello world"
    assert result.is_reliable is True


def test_fake_stt_returns_mapped_transcription() -> None:
    client = FakeSTT().with_mapping(b"unique", "mapped text")
    result = client.transcribe(b"unique", "audio/wav")
    assert result.text == "mapped text"
    assert result.is_reliable is True


def test_fake_stt_is_deterministic() -> None:
    client = FakeSTT()
    first = client.transcribe(b"x", "audio/wav")
    second = client.transcribe(b"x", "audio/wav")
    assert first.text == second.text
    assert first.is_reliable == second.is_reliable


def test_openai_stt_returns_transcription() -> None:
    mock_response = MagicMock()
    mock_response.text = "  transcribed text  "
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_response

    client = OpenAISpeechToText(api_key="test-key")
    client._client = mock_client
    result = client.transcribe(b"audio", "audio/wav")

    assert result.text == "transcribed text"
    assert result.is_reliable is True


def test_openai_stt_returns_fallback_on_empty_transcription() -> None:
    mock_response = MagicMock()
    mock_response.text = "   "
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_response

    client = OpenAISpeechToText(api_key="test-key")
    client._client = mock_client
    result = client.transcribe(b"audio", "audio/wav")

    assert result.is_reliable is False
    assert result.fallback_message is not None


def test_openai_stt_returns_fallback_on_api_error() -> None:
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.side_effect = RuntimeError("API down")

    client = OpenAISpeechToText(api_key="test-key")
    client._client = mock_client
    result = client.transcribe(b"audio", "audio/wav")

    assert result.is_reliable is False
    assert result.fallback_message is not None


@pytest.mark.live_speech
@pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="GROQ_API_KEY is not configured")
def test_openai_stt_handles_invalid_api_key() -> None:
    client = OpenAISpeechToText(api_key="invalid-key-for-testing")
    result = client.transcribe(b"not-audio", "audio/wav")
    assert result.is_reliable is False
    assert result.fallback_message is not None

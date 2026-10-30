"""Unit tests for LLM configuration and adapter construction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from banking_support.agents.llm import (
    OpenAIExtractor,
    OpenAISupportIntentClassifier,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from banking_support.api.app import AppState
from banking_support.config import Settings


class TestSettings:
    def test_llm_api_key_reads_from_groq_api_key(self) -> None:
        settings = Settings(_env_file=None, GROQ_API_KEY="gsk_secret")
        assert settings.llm_api_key == "gsk_secret"

    def test_llm_api_key_defaults_to_none(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.llm_api_key is None

    def test_empty_llm_api_key_is_normalised_to_none(self) -> None:
        settings = Settings(_env_file=None, GROQ_API_KEY="")
        assert settings.llm_api_key is None

    def test_voice_input_types_accept_json_list(self) -> None:
        settings = Settings(
            _env_file=None,
            VOICE_SUPPORTED_INPUT_TYPES='["audio/wav","audio/webm"]',
        )
        assert settings.voice_supported_input_types == frozenset({"audio/wav", "audio/webm"})

    def test_voice_input_types_accept_comma_separated_value(self) -> None:
        settings = Settings(
            _env_file=None,
            VOICE_SUPPORTED_INPUT_TYPES="audio/wav,audio/webm",
        )
        assert settings.voice_supported_input_types == frozenset({"audio/wav", "audio/webm"})

    def test_llm_model_defaults_to_groq_model(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.llm_model == "openai/gpt-oss-20b"

    def test_llm_model_reads_from_env(self) -> None:
        settings = Settings(_env_file=None, LLM_MODEL="openai/gpt-oss-20b")
        assert settings.llm_model == "openai/gpt-oss-20b"

    def test_llm_base_url_defaults_to_groq(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.llm_base_url == "https://api.groq.com/openai/v1"

    def test_llm_base_url_reads_from_env(self) -> None:
        settings = Settings(_env_file=None, LLM_BASE_URL="https://example.com/v1")
        assert settings.llm_base_url == "https://example.com/v1"

    def test_llm_temperature_defaults_to_zero(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.llm_temperature == 0.0

    def test_llm_temperature_reads_from_env(self) -> None:
        settings = Settings(_env_file=None, LLM_TEMPERATURE="0.5")
        assert settings.llm_temperature == 0.5


class TestAppStateWiring:
    def test_build_extractor_uses_openai_when_key_present(self) -> None:
        settings = Settings(
            _env_file=None,
            GROQ_API_KEY="gsk_secret",
            LLM_MODEL="openai/gpt-oss-20b",
            LLM_BASE_URL="https://api.groq.com/openai/v1",
            LLM_TEMPERATURE="0.0",
        )
        extractor = AppState._build_extractor(settings)
        assert isinstance(extractor, OpenAIExtractor)

    def test_build_extractor_falls_back_to_fake_when_key_missing(self) -> None:
        settings = Settings(_env_file=None)
        extractor = AppState._build_extractor(settings)
        assert isinstance(extractor, ScriptedFakeExtractor)

    def test_build_classifier_uses_openai_when_key_present(self) -> None:
        settings = Settings(
            _env_file=None,
            GROQ_API_KEY="gsk_secret",
            LLM_MODEL="openai/gpt-oss-20b",
            LLM_BASE_URL="https://api.groq.com/openai/v1",
            LLM_TEMPERATURE="0.0",
        )
        classifier = AppState._build_intent_classifier(settings)
        assert isinstance(classifier, OpenAISupportIntentClassifier)

    def test_build_classifier_falls_back_to_fake_when_key_missing(self) -> None:
        settings = Settings(_env_file=None)
        classifier = AppState._build_intent_classifier(settings)
        assert isinstance(classifier, ScriptedFakeSupportIntentClassifier)


class TestOpenAIExtractorConstruction:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            OpenAIExtractor(api_key="")

    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_constructs_chat_openai_with_params(self, mock_chat: MagicMock) -> None:
        OpenAIExtractor(
            api_key="gsk_secret",
            model="openai/gpt-oss-20b",
            base_url="https://api.groq.com/openai/v1",
            temperature=0.0,
        )
        mock_chat.assert_called_once_with(
            api_key="gsk_secret",
            model="openai/gpt-oss-20b",
            base_url="https://api.groq.com/openai/v1",
            temperature=0.0,
        )

    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_invokes_chat_openai_for_extraction(self, mock_chat: MagicMock) -> None:
        extractor = OpenAIExtractor(api_key="gsk_secret")
        extractor.extract("hello")
        mock_chat.return_value.with_structured_output.assert_called_once()
        mock_chat.return_value.with_structured_output.return_value.invoke.assert_called_once()


class TestOpenAISupportIntentClassifierConstruction:
    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            OpenAISupportIntentClassifier(api_key="")

    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_constructs_chat_openai_with_params(self, mock_chat: MagicMock) -> None:
        OpenAISupportIntentClassifier(
            api_key="gsk_secret",
            model="openai/gpt-oss-20b",
            base_url="https://api.groq.com/openai/v1",
            temperature=0.0,
        )
        mock_chat.assert_called_once_with(
            api_key="gsk_secret",
            model="openai/gpt-oss-20b",
            base_url="https://api.groq.com/openai/v1",
            temperature=0.0,
        )

    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_invokes_chat_openai_for_classification(self, mock_chat: MagicMock) -> None:
        classifier = OpenAISupportIntentClassifier(api_key="gsk_secret")
        classifier.classify("hello")
        mock_chat.return_value.with_structured_output.assert_called_once()
        mock_chat.return_value.with_structured_output.return_value.invoke.assert_called_once()


class TestAdapterFallbackBehavior:
    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_extractor_returns_chitchat_on_error(self, mock_chat: MagicMock) -> None:
        mock_chat.return_value.invoke.side_effect = RuntimeError("provider down")
        extractor = OpenAIExtractor(api_key="gsk_secret")
        result = extractor.extract("hello")
        assert result.intent.name == "CHITCHAT"

    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_classifier_returns_uninterpretable_on_error(self, mock_chat: MagicMock) -> None:
        mock_chat.return_value.invoke.side_effect = RuntimeError("provider down")
        classifier = OpenAISupportIntentClassifier(api_key="gsk_secret")
        result = classifier.classify("hello")
        assert result.intent.name == "UNINTERPRETABLE"


class TestCredentialLeakagePrevention:
    @patch("banking_support.agents.llm.ChatOpenAI")
    def test_api_key_not_included_in_fallback_response(self, mock_chat: MagicMock) -> None:
        mock_chat.return_value.invoke.side_effect = RuntimeError(
            "Unauthorized: invalid key gsk_secret"
        )
        extractor = OpenAIExtractor(api_key="gsk_secret")
        result = extractor.extract("hello")
        assert "gsk_secret" not in str(result)
        assert result.intent.name == "CHITCHAT"

"""Tests for provider-native structured model output boundaries."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from healthcare_support.agents.llm import (
    ExtractionResult,
    OpenAIExtractor,
    OpenAISupportIntentClassifier,
)
from healthcare_support.domain.conversation import ExtractionIntent
from healthcare_support.domain.routing import IntentClassification, SupportIntent


@patch("healthcare_support.agents.llm.ChatOpenAI")
def test_extractor_uses_native_structured_output(mock_chat: MagicMock) -> None:
    structured = mock_chat.return_value.with_structured_output.return_value
    structured.invoke.return_value = {
        "parsed": ExtractionResult(intent=ExtractionIntent.ANSWER_SECRET, secret_answer="Yoda"),
        "raw": None,
        "parsing_error": None,
    }

    result = OpenAIExtractor(api_key="test").extract("It is Yoda")

    assert result.intent == ExtractionIntent.ANSWER_SECRET
    assert result.secret_answer == "Yoda"
    mock_chat.return_value.with_structured_output.assert_called_once_with(
        ExtractionResult, include_raw=True
    )


@patch("healthcare_support.agents.llm.ChatOpenAI")
def test_classifier_fails_safe_for_invalid_structured_output(mock_chat: MagicMock) -> None:
    structured = mock_chat.return_value.with_structured_output.return_value
    structured.invoke.return_value = {"parsed": None, "raw": None, "parsing_error": "invalid"}

    result = OpenAISupportIntentClassifier(api_key="test").classify("unknown")

    assert result.intent == SupportIntent.UNINTERPRETABLE


def test_models_remain_advisory_contracts() -> None:
    result = ExtractionResult(intent=ExtractionIntent.PROVIDE_IDENTIFICATION, name="Ada")
    classification = IntentClassification(intent=SupportIntent.GENERAL_BANKING)

    assert result.name == "Ada"
    assert classification.intent == SupportIntent.GENERAL_BANKING

"""Unit tests for support-intent classification models and fakes."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from healthcare_support.agents.llm import (
    IntentClassification as AgentIntentClassification,
)
from healthcare_support.agents.llm import (
    ScriptedFakeSupportIntentClassifier,
)
from healthcare_support.domain.routing import IntentClassification, SupportIntent


class TestIntentClassificationModel:
    def test_valid_supported_intent(self) -> None:
        result = IntentClassification(intent=SupportIntent.YACHT_INSURANCE)
        assert result.intent == SupportIntent.YACHT_INSURANCE
        assert result.needs_clarification is False

    def test_ambiguous_requires_clarification_flag(self) -> None:
        with pytest.raises(ValidationError):
            IntentClassification(intent=SupportIntent.AMBIGUOUS)

    def test_ambiguous_requires_clarification_prompt(self) -> None:
        with pytest.raises(ValidationError):
            IntentClassification(
                intent=SupportIntent.AMBIGUOUS,
                needs_clarification=True,
            )

    def test_ambiguous_with_prompt_is_valid(self) -> None:
        result = IntentClassification(
            intent=SupportIntent.AMBIGUOUS,
            needs_clarification=True,
            clarification_prompt="Could you clarify?",
        )
        assert result.clarification_prompt == "Could you clarify?"

    def test_specialization_is_optional(self) -> None:
        result = IntentClassification(
            intent=SupportIntent.OTHER_SPECIALIZED,
            specialization="yacht_insurance",
        )
        assert result.specialization == "yacht_insurance"


class TestScriptedFakeClassifier:
    def test_returns_scripted_results_in_order(self) -> None:
        classifier = ScriptedFakeSupportIntentClassifier(
            [
                IntentClassification(intent=SupportIntent.YACHT_INSURANCE),
                IntentClassification(intent=SupportIntent.ACCOUNT_ASSISTANCE),
            ]
        )
        assert classifier.classify("first").intent == SupportIntent.YACHT_INSURANCE
        assert classifier.classify("second").intent == SupportIntent.ACCOUNT_ASSISTANCE

    def test_falls_back_to_uninterpretable(self) -> None:
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.INSURANCE)]
        )
        classifier.classify("first")
        fallback = classifier.classify("second")
        assert fallback.intent == SupportIntent.UNINTERPRETABLE

    def test_empty_script_returns_uninterpretable(self) -> None:
        classifier = ScriptedFakeSupportIntentClassifier([])
        result = classifier.classify("anything")
        assert result.intent == SupportIntent.UNINTERPRETABLE


class TestAgentImports:
    def test_agent_intent_classification_alias(self) -> None:
        # The agent module re-exports the domain model for convenience.
        result = AgentIntentClassification(intent=SupportIntent.GENERAL_BANKING)
        assert result.intent == SupportIntent.GENERAL_BANKING

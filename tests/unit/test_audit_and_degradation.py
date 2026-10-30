"""Unit tests for audit recording and safe degradation (US5)."""

from __future__ import annotations

import pytest

from banking_support.core.advanced_guardrails import AdvancedGuardrailEvaluator
from banking_support.domain.advanced_guardrails import AdvancedGuardrailInput, ConversationContext
from banking_support.domain.conversation import ConversationStatus
from banking_support.domain.guardrails import GuardrailInput


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _advanced_input(
    content: str, *, content_type: str = "customer_input"
) -> AdvancedGuardrailInput:
    guardrail_input = GuardrailInput(
        content=content,
        content_type=content_type,
        conversation_id="us5-conv",
        status=ConversationStatus.AUTHENTICATED,
        messages=[],
    )
    return AdvancedGuardrailInput(
        guardrail_input=guardrail_input,
        conversation_context=ConversationContext(),
    )


class TestDecisionRecording:
    def test_blocked_decision_records_reason_category(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        decision = evaluator.evaluate(_advanced_input("Recommend a movie"))
        assert decision.reason_category == "off_topic"
        assert decision.outcome.value == "blocked"
        assert len(decision.check_results) > 0

    def test_audit_metadata_has_no_message_content(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        decision = evaluator.evaluate(_advanced_input("Recommend a movie"))
        meta_str = str(decision.audit_metadata)
        assert "Recommend a movie" not in meta_str

    def test_allowed_decision_records_content_type(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        decision = evaluator.evaluate(_advanced_input("I need help with my account"))
        assert decision.outcome.value == "allowed"
        assert decision.audit_metadata.get("content_type") == "customer_input"


class TestSafeDegradation:
    def test_exception_in_classifier_degrades_to_allowed(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        # Force the topic classifier to raise by replacing it with a broken callable.
        original = evaluator._topic_classifier.classify
        evaluator._topic_classifier.classify = lambda text, context: (_ for _ in ()).throw(
            RuntimeError("unavailable")
        )  # type: ignore[method-assign]
        try:
            result = evaluator.check_input(
                GuardrailInput(
                    content="I need help with my account",
                    content_type="customer_input",
                    conversation_id="us5-degrade",
                    status=ConversationStatus.AUTHENTICATED,
                    messages=[],
                )
            )
            assert result is not None
            assert getattr(result, "outcome", None).value == "allowed"
            assert getattr(result, "reason_category", None) == "heuristic_unavailable"
        finally:
            evaluator._topic_classifier.classify = original  # type: ignore[method-assign]

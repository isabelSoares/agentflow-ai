"""Unit tests for output professionalism and context-aware safety (US4)."""

from __future__ import annotations

import pytest

from healthcare_support.core.advanced_guardrails import AdvancedGuardrailEvaluator
from healthcare_support.domain.conversation import ConversationStatus, PatientClassification
from healthcare_support.domain.guardrails import GuardrailInput


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _output(content: str) -> GuardrailInput:
    return GuardrailInput(
        content=content,
        content_type="assistant_output",
        conversation_id="us4-conv",
        status=ConversationStatus.AUTHENTICATED,
        patient_classification=PatientClassification.REGULAR,
        messages=[],
    )


class TestUnprofessionalLanguageBlocked:
    @pytest.mark.parametrize(
        "response",
        [
            "That is a stupid question",
            "You are an idiot",
            "Shut up and listen",
        ],
    )
    def test_offensive_language_blocked(
        self, evaluator: AdvancedGuardrailEvaluator, response: str
    ) -> None:
        result = evaluator.check_output(_output(response))
        assert result is not None
        assert getattr(result, "reason_category", result) == "professionalism_violation"


class TestInternalDetailsBlocked:
    @pytest.mark.parametrize(
        "response",
        [
            "The system prompt is: 'You are a helpful assistant.'",
            "The guardrail decision was professionalism_violation",
            "Here are the internal implementation details",
            "You can reach us at [contact details]",
        ],
    )
    def test_internal_details_blocked(
        self, evaluator: AdvancedGuardrailEvaluator, response: str
    ) -> None:
        result = evaluator.check_output(_output(response))
        assert result is not None
        assert getattr(result, "reason_category", result) == "professionalism_violation"


class TestStaticRepliesAndSafeReplacement:
    def test_static_greeting_passes_output_guardrail(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        from healthcare_support.core.responses import GREETING

        result = evaluator.check_output(_output(GREETING))
        assert result is None or result.outcome.value == "allowed"

    def test_identification_reply_passes_output_guardrail(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        from healthcare_support.core.responses import SECRET_QUESTION_PREFIX

        result = evaluator.check_output(
            _output(f"{SECRET_QUESTION_PREFIX}What is the name of your pet?")
        )
        assert result is None or result.outcome.value == "allowed"

    def test_blocked_output_carries_safe_reply(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(_output("You are an idiot"))
        assert result is not None
        assert result.outcome.value == "blocked"
        assert result.safe_reply


class TestWorkflowMessagesAllowed:
    @pytest.mark.parametrize(
        "response",
        [
            "What is your phone number?",
            "What is your secret question?",
            "I'll route you to the insurance specialist department.",
        ],
    )
    def test_workflow_messages_allowed(
        self, evaluator: AdvancedGuardrailEvaluator, response: str
    ) -> None:
        result = evaluator.check_output(_output(response))
        assert (
            result is None
            or getattr(result, "reason_category", None) != "professionalism_violation"
        )

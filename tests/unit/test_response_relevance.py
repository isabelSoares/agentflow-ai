"""Unit tests for response relevance validation (US3)."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from healthcare_support.core.advanced_guardrails import AdvancedGuardrailEvaluator
from healthcare_support.domain.conversation import ConversationStatus, PatientClassification
from healthcare_support.domain.guardrails import GuardrailInput
from healthcare_support.domain.routing import SupportIntent


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _output(
    response: str,
    request: str,
    *,
    status: ConversationStatus = ConversationStatus.AUTHENTICATED,
    classification: PatientClassification | None = None,
    intent: SupportIntent | None = None,
) -> GuardrailInput:
    return GuardrailInput(
        content=response,
        content_type="assistant_output",
        conversation_id="us3-conv",
        status=status,
        patient_classification=classification,
        support_intent=intent,
        messages=[HumanMessage(content=request)],
    )


class TestRelevantResponsesAllowed:
    def test_response_matching_request_allowed(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(
            _output(
                "Insurance coverage is available through our insurance and billing specialists.",
                "Can you tell me about insurance coverage?",
                intent=SupportIntent.SPECIALIST_REFERRAL,
            )
        )
        assert result is None or getattr(result, "reason_category", None) != "relevance_failure"

    def test_general_routing_response_allowed(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(
            _output(
                "I'll connect you with the appropriate department.",
                "I need help scheduling an appointment",
                intent=SupportIntent.APPOINTMENT_ASSISTANCE,
            )
        )
        assert result is None or getattr(result, "reason_category", None) != "relevance_failure"


class TestIrrelevantResponsesBlocked:
    def test_billing_response_to_insurance_question_blocked(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_output(
            _output(
                "Our invoice processing costs start at 3.5%.",
                "Can you tell me about insurance coverage?",
                intent=SupportIntent.SPECIALIST_REFERRAL,
            )
        )
        assert result is not None
        assert getattr(result, "reason_category", result) == "relevance_failure"


class TestWorkflowMessagesPreserved:
    def test_verification_question_preserved(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(
            _output(
                "What is your phone number?",
                "My name is Alice",
                status=ConversationStatus.COLLECTING,
            )
        )
        assert result is None or getattr(result, "reason_category", None) != "relevance_failure"

    def test_routing_explanation_preserved(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(
            _output(
                "I'll route you to the Insurance and Billing Department.",
                "I need insurance help",
                intent=SupportIntent.INSURANCE,
            )
        )
        assert result is None or getattr(result, "reason_category", None) != "relevance_failure"


class TestStateContradictionBlocked:
    def test_authenticated_claim_when_not_authenticated_blocked(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_output(
            _output(
                "You are now authenticated.",
                "My name is Alice",
                status=ConversationStatus.COLLECTING,
            )
        )
        assert result is not None
        assert getattr(result, "reason_category", result) == "relevance_failure"

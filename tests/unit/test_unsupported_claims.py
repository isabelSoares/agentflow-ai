"""Unit tests for unsupported-claim detection (US3)."""

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
        conversation_id="us3-claims",
        status=ConversationStatus.AUTHENTICATED,
        patient_classification=PatientClassification.REGULAR,
        messages=[],
    )


class TestUnsupportedClaimsBlocked:
    @pytest.mark.parametrize(
        "response",
        [
            "Our healthcare provider guarantees a 15% faster recovery",
            "Your insurance claim is guaranteed approval",
            "The reimbursement rate is fixed at 2%",
            "The billing fee is €500",
            "You are eligible for a €100000 coverage amount",
            "Your referral has been completed",
        ],
    )
    def test_unsupported_claims_blocked(
        self, evaluator: AdvancedGuardrailEvaluator, response: str
    ) -> None:
        result = evaluator.check_output(_output(response))
        assert result is not None
        assert getattr(result, "reason_category", result) == "unsupported_claim"


class TestVerifiedAndGeneralClaimsAllowed:
    def test_verified_catalog_statement_allowed(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_output(
            _output(
                "Insurance coverage is available through our insurance and billing specialists."
            )
        )
        assert result is None or getattr(result, "reason_category", None) != "unsupported_claim"

    def test_general_informational_explanation_allowed(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_output(
            _output("Specialist referrals usually require a clinical assessment.")
        )
        assert result is None or getattr(result, "reason_category", None) != "unsupported_claim"

    def test_missing_coverage_fallback(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(
            _output("We guarantee approval for our new premium care plan.")
        )
        assert result is not None
        assert getattr(result, "reason_category", result) == "unsupported_claim"

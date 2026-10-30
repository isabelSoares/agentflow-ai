"""Unit tests for unsupported-claim detection (US3)."""

from __future__ import annotations

import pytest

from banking_support.core.advanced_guardrails import AdvancedGuardrailEvaluator
from banking_support.domain.conversation import ConversationStatus, CustomerClassification
from banking_support.domain.guardrails import GuardrailInput


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _output(content: str) -> GuardrailInput:
    return GuardrailInput(
        content=content,
        content_type="assistant_output",
        conversation_id="us3-claims",
        status=ConversationStatus.AUTHENTICATED,
        customer_classification=CustomerClassification.REGULAR,
        messages=[],
    )


class TestUnsupportedClaimsBlocked:
    @pytest.mark.parametrize(
        "response",
        [
            "Our bank guarantees a 15% annual return",
            "Your loan is guaranteed approval",
            "The interest rate is fixed at 2%",
            "The annual fee is €500",
            "You are eligible for a €100000 loan",
            "Your transfer has been completed",
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
            _output("Yacht insurance is available through our marine insurance specialists.")
        )
        assert result is None or getattr(result, "reason_category", None) != "unsupported_claim"

    def test_general_informational_explanation_allowed(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_output(
            _output("Loans usually require an application and a credit check.")
        )
        assert result is None or getattr(result, "reason_category", None) != "unsupported_claim"

    def test_missing_coverage_fallback(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_output(
            _output("We guarantee approval for our new platinum savings account.")
        )
        assert result is not None
        assert getattr(result, "reason_category", result) == "unsupported_claim"

"""Integration tests for User Story 5: audit and safe degradation."""

from __future__ import annotations

from healthcare_support.core.guardrails import GuardrailEvaluator
from healthcare_support.data.policies import default_banking_policy
from healthcare_support.domain.conversation import ConversationStatus
from healthcare_support.domain.guardrails import GuardrailInput


def _input(content: str) -> GuardrailInput:
    return GuardrailInput(
        content=content,
        content_type="patient_input",
        conversation_id="us5-conv",
        status=ConversationStatus.COLLECTING,
        messages=[],
    )


class TestDeterministicBlockDespiteUnavailableHeuristic:
    def test_unauthenticated_data_request_blocked_when_heuristic_fails(self) -> None:
        def failing_checker(_input: GuardrailInput) -> bool:
            raise RuntimeError("LLM unavailable")

        evaluator = GuardrailEvaluator(
            policy_rules=default_banking_policy(),
            heuristic_input_checker=failing_checker,
            safe_replies={"data_request_refusal": "Please verify your identity first."},
        )
        result = evaluator.evaluate(_input("What is my balance?"))
        assert result.outcome.value == "blocked"
        assert result.reason_category == "unauthenticated"


class TestAuditMetadata:
    def test_advanced_block_records_distinguishable_reason(self) -> None:
        from healthcare_support.services.guardrails_service import build_guardrail_evaluator

        evaluator = build_guardrail_evaluator()
        result = evaluator.evaluate(_input("Recommend a movie"))
        assert result.outcome.value == "blocked"
        assert result.reason_category == "off_topic"
        check_results = result.audit_metadata.get("check_results", [])
        assert any(r.get("reason_category") == "off_topic" for r in check_results)
        # No message content leaked into audit metadata.
        meta_str = str(result.audit_metadata)
        assert "Recommend a movie" not in meta_str

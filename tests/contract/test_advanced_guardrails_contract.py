"""Contract tests for Advanced Guardrails interfaces."""

from __future__ import annotations

import pytest

from healthcare_support.config.trusted_healthcare_info import get_catalog
from healthcare_support.core.advanced_guardrails import (
    AdvancedGuardrailEvaluator,
    RedirectionStateTracker,
    make_advanced_guardrail_checkers,
)
from healthcare_support.domain.advanced_guardrails import (
    CoverageStatus,
    TrustedHealthcareCatalog,
    TrustedHealthcareEntry,
)
from healthcare_support.domain.conversation import ConversationStatus, PatientClassification
from healthcare_support.domain.guardrails import GuardrailDecisionOutcome, GuardrailInput
from healthcare_support.domain.routing import SupportIntent


@pytest.fixture
def evaluator() -> AdvancedGuardrailEvaluator:
    return AdvancedGuardrailEvaluator()


def _input(
    content: str,
    *,
    content_type: str = "patient_input",
    status: ConversationStatus = ConversationStatus.COLLECTING,
    classification: PatientClassification | None = None,
    intent: SupportIntent | None = None,
) -> GuardrailInput:
    return GuardrailInput(
        content=content,
        content_type=content_type,
        conversation_id="test-conv",
        status=status,
        patient_classification=classification,
        support_intent=intent,
        messages=[],
    )


class TestHeuristicCheckerContract:
    """Contract 1: heuristic checker callable signature."""

    def test_input_checker_returns_block_reason_for_off_topic(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_input(_input("Recommend a movie"))
        assert result is not None
        assert isinstance(result, str) or hasattr(result, "outcome")
        if isinstance(result, str):
            assert result == "off_topic"

    def test_input_checker_returns_none_for_allowed(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_input(_input("Hello, I need help scheduling an appointment"))
        assert result is None or result is False

    def test_output_checker_returns_block_reason_for_unsupported_claim(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_output(
            _input(
                "Our healthcare provider guarantees a 15% faster recovery",
                content_type="assistant_output",
                status=ConversationStatus.AUTHENTICATED,
                classification=PatientClassification.REGULAR,
            )
        )
        assert result is not None

    def test_checker_does_not_mutate_input(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        input_ = _input("Recommend a movie")
        original = input_.model_dump()
        evaluator.check_input(input_)
        assert input_.model_dump() == original


class TestTrustedHealthcareCatalogContract:
    """Contract 3: trusted catalog lookup and claim coverage."""

    def test_lookup_returns_missing_entry_for_unknown_topic(self) -> None:
        catalog = get_catalog("default")
        entry = catalog.lookup("unknown_topic")
        assert entry.coverage_status == CoverageStatus.MISSING

    def test_covers_claim_returns_supported_for_verified_statement(self) -> None:
        catalog = TrustedHealthcareCatalog(
            catalog_id="test",
            entries={
                "copay": TrustedHealthcareEntry(
                    topic="copay",
                    verified_statements=["Our copay for a specialist visit is $40."],
                    coverage_status=CoverageStatus.COMPLETE,
                ),
            },
        )
        result = catalog.covers_claim("Our copay for a specialist visit is $40.")
        assert result.is_supported is True

    def test_covers_claim_returns_unsupported_for_high_risk_claim(self) -> None:
        catalog = get_catalog("default")
        result = catalog.covers_claim("We guarantee a 15% faster recovery")
        assert result.is_high_risk is True
        assert result.is_supported is False


class TestRedirectionStateTrackerContract:
    """Contract 4: redirection loop prevention."""

    def test_first_off_topic_uses_full_style(self) -> None:
        tracker = RedirectionStateTracker()
        state = tracker.record("conv-1", "off_topic")
        assert state.consecutive_off_topic_count == 1
        assert tracker.reply_style(state) == "full"

    def test_second_off_topic_uses_brief_style(self) -> None:
        tracker = RedirectionStateTracker()
        tracker.record("conv-1", "off_topic")
        state = tracker.record("conv-1", "off_topic")
        assert state.consecutive_off_topic_count == 2
        assert tracker.reply_style(state) == "brief"

    def test_allowed_resets_counter(self) -> None:
        tracker = RedirectionStateTracker()
        tracker.record("conv-1", "off_topic")
        state = tracker.record("conv-1", "allowed")
        assert state.consecutive_off_topic_count == 0

    def test_tracker_does_not_store_message_content(self) -> None:
        tracker = RedirectionStateTracker()
        state = tracker.record("conv-1", "off_topic")
        assert "message" not in state.model_dump()


class TestGuardrailOutputContract:
    """Contract 2/5: outcome vocabulary and safe reply constraints."""

    def test_factory_returns_callables(self) -> None:
        input_checker, output_checker = make_advanced_guardrail_checkers()
        assert callable(input_checker)
        assert callable(output_checker)

    def test_blocked_output_has_safe_reply(self, evaluator: AdvancedGuardrailEvaluator) -> None:
        result = evaluator.check_input(_input("Recommend a movie"))
        assert result is not None
        if hasattr(result, "outcome"):
            assert result.outcome == GuardrailDecisionOutcome.BLOCKED
            assert result.safe_reply is not None
            assert len(result.safe_reply) > 0

    def test_reason_category_from_fixed_vocabulary(
        self, evaluator: AdvancedGuardrailEvaluator
    ) -> None:
        result = evaluator.check_input(_input("Recommend a movie"))
        if hasattr(result, "reason_category"):
            assert result.reason_category in {
                "off_topic",
                "needs_clarification",
                "harmful_content",
                "relevance_failure",
                "unsupported_claim",
                "professionalism_violation",
                "heuristic_unavailable",
            }

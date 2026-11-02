"""Service factory for wiring the GuardrailEvaluator with advanced checks."""

from __future__ import annotations

from healthcare_support.config.safe_replies import DEFAULT_ADVANCED_SAFE_REPLIES
from healthcare_support.config.trusted_healthcare_info import get_catalog
from healthcare_support.core.advanced_guardrails import (
    RedirectionStateTracker,
    make_advanced_guardrail_checkers,
)
from healthcare_support.core.guardrails import GuardrailEvaluator
from healthcare_support.core.responses import (
    DATA_REQUEST_REFUSAL,
    INTERNAL_DISCLOSURE_REFUSAL,
    MANIPULATION_RE_PROMPT,
    NON_PATIENT_RESPONSE,
    PREMIUM_RESTRICTION_MESSAGE,
    PRIVACY_VIOLATION_MESSAGE,
    PROHIBITED_ACTION_MESSAGE,
    UNAVAILABLE_GUARDIAL_MESSAGE,
)
from healthcare_support.data.policies import default_healthcare_policy
from healthcare_support.domain.advanced_guardrails import TrustedHealthcareCatalog

_DEFAULT_SAFE_REPLIES: dict[str, str] = {
    "manipulation": MANIPULATION_RE_PROMPT,
    "internal_disclosure": INTERNAL_DISCLOSURE_REFUSAL,
    "data_request_refusal": DATA_REQUEST_REFUSAL,
    "non_patient": NON_PATIENT_RESPONSE,
    "premium_restriction": PREMIUM_RESTRICTION_MESSAGE,
    "prohibited_action": PROHIBITED_ACTION_MESSAGE,
    "privacy": PRIVACY_VIOLATION_MESSAGE,
    "unavailable": UNAVAILABLE_GUARDIAL_MESSAGE,
}


def build_guardrail_evaluator(
    catalog: TrustedHealthcareCatalog | None = None,
    safe_replies: dict[str, str] | None = None,
    redirection_tracker: RedirectionStateTracker | None = None,
) -> GuardrailEvaluator:
    """Return a GuardrailEvaluator with deterministic and advanced checks wired.

    The advanced checks are stateless heuristic classifiers that extend the
    existing evaluator. They run only after deterministic checks pass and can
    never override a deterministic block.
    """
    resolved_catalog = catalog or get_catalog("default")
    resolved_safe_replies = {**_DEFAULT_SAFE_REPLIES, **DEFAULT_ADVANCED_SAFE_REPLIES}
    if safe_replies:
        resolved_safe_replies.update(safe_replies)

    input_checker, output_checker = make_advanced_guardrail_checkers(
        catalog=resolved_catalog,
        safe_replies=resolved_safe_replies,
        redirection_tracker=redirection_tracker,
    )

    return GuardrailEvaluator(
        policy_rules=default_healthcare_policy(),
        heuristic_input_checker=input_checker,
        heuristic_output_checker=output_checker,
        safe_replies=resolved_safe_replies,
    )


__all__ = ["build_guardrail_evaluator"]

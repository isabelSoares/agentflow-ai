"""Advanced Guardrails domain: evaluation inputs, outputs, catalog, and decisions.

All models are pure data structures with no business logic or external dependencies.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import StrEnum
from typing import Any, Literal, cast

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from healthcare_support.domain.conversation import ConversationStatus, PatientClassification
from healthcare_support.domain.guardrails import GuardrailDecisionOutcome, GuardrailInput
from healthcare_support.domain.routing import SupportIntent


class CoverageStatus(StrEnum):
    """Coverage status of a trusted healthcare information entry."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


class CheckVerdict(StrEnum):
    """Verdict of an individual advanced guardrail check."""

    PASS = "pass"
    BLOCK = "block"
    CLARIFY = "clarify"
    UNAVAILABLE = "unavailable"


class ConversationContext(BaseModel):
    """Trusted state surrounding the message being evaluated."""

    model_config = ConfigDict(frozen=True)

    current_agent: Literal["greeter", "bouncer", "specialist"] = Field(
        default="greeter",
        description="Agent step that produced or is handling the message.",
    )
    status: ConversationStatus = Field(
        default=ConversationStatus.COLLECTING,
        description="Trusted authentication status from the Greeter.",
    )
    patient_classification: PatientClassification | None = Field(
        default=None,
        description="Trusted tier classification from the Bouncer.",
    )
    support_intent: SupportIntent | None = Field(
        default=None,
        description="Current pending support intent, when available.",
    )
    recent_messages: Sequence[BaseMessage] = Field(
        default_factory=tuple,
        description="Bounded recent conversation history.",
    )
    has_collected_attributes: bool = Field(
        default=False,
        description="True when the greeter has collected some identification attributes.",
    )

    @field_validator("recent_messages", mode="before")
    @classmethod
    def _bound_history(cls, value: object) -> Sequence[BaseMessage]:
        if value is None:
            return ()
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(cast(Sequence[BaseMessage], value)[-12:])
        return tuple(cast(Sequence[BaseMessage], value))


class TrustedHealthcareEntry(BaseModel):
    """A single topic in the trusted healthcare-information catalog."""

    model_config = ConfigDict(frozen=True)

    topic: str = Field(min_length=1)
    verified_statements: Sequence[str] = Field(default_factory=tuple)
    coverage_status: CoverageStatus = Field(default=CoverageStatus.MISSING)

    @model_validator(mode="after")
    def _consistent_coverage(self) -> TrustedHealthcareEntry:
        if not self.verified_statements:
            object.__setattr__(self, "coverage_status", CoverageStatus.MISSING)
        return self


class RiskPattern(BaseModel):
    """A pattern that flags a healthcare-specific claim as high-risk."""

    model_config = ConfigDict(frozen=True)

    pattern: str = Field(min_length=1)
    reason_category: str = Field(default="unsupported_claim")
    examples: Sequence[str] = Field(default_factory=tuple)


class CoverageResult(BaseModel):
    """Result of verifying a claim against the trusted catalog."""

    model_config = ConfigDict(frozen=True)

    is_supported: bool = False
    is_high_risk: bool = False
    matched_pattern: str | None = None
    matched_statement: str | None = None
    coverage_status: CoverageStatus = CoverageStatus.MISSING


class TrustedHealthcareCatalog(BaseModel):
    """Authoritative facts used to verify healthcare-specific claims."""

    model_config = ConfigDict(frozen=True)

    catalog_id: str = Field(min_length=1)
    entries: dict[str, TrustedHealthcareEntry] = Field(default_factory=dict)
    risk_patterns: Sequence[RiskPattern] = Field(default_factory=tuple)

    def lookup(self, topic: str) -> TrustedHealthcareEntry:
        """Return the entry for a topic, or a missing entry if unknown."""
        return self.entries.get(
            topic,
            TrustedHealthcareEntry(topic=topic, coverage_status=CoverageStatus.MISSING),
        )

    def covers_claim(self, claim_text: str) -> CoverageResult:
        """Check whether a claim is high-risk and whether it is supported."""
        lowered = claim_text.casefold()

        matched_pattern: str | None = None
        for risk in self.risk_patterns:
            if re.search(risk.pattern, lowered, re.IGNORECASE):
                matched_pattern = risk.pattern
                break

        if matched_pattern is None:
            return CoverageResult(is_supported=True, is_high_risk=False)

        # High-risk claim: look for a verified statement that matches the claim.
        for entry in self.entries.values():
            for statement in entry.verified_statements:
                if statement.casefold() in lowered:
                    return CoverageResult(
                        is_supported=True,
                        is_high_risk=True,
                        matched_pattern=matched_pattern,
                        matched_statement=statement,
                        coverage_status=entry.coverage_status,
                    )

        return CoverageResult(
            is_supported=False,
            is_high_risk=True,
            matched_pattern=matched_pattern,
            coverage_status=CoverageStatus.MISSING,
        )


class AdvancedGuardrailInput(BaseModel):
    """Everything needed for an advanced guardrails evaluation."""

    model_config = ConfigDict(frozen=True)

    guardrail_input: GuardrailInput
    conversation_context: ConversationContext = Field(
        default_factory=ConversationContext,
    )
    trusted_catalog_ref: str = Field(default="default")


class CheckResult(BaseModel):
    """Result of an individual advanced check."""

    model_config = ConfigDict(frozen=True)

    check_name: str = Field(min_length=1)
    verdict: CheckVerdict
    reason_category: str | None = Field(default=None)
    confidence: str = Field(default="high")

    @field_validator("confidence")
    @classmethod
    def _valid_confidence(cls, value: str) -> str:
        if value not in {"high", "medium", "low"}:
            raise ValueError("confidence must be high, medium, or low")
        return value


class AdvancedGuardrailDecision(BaseModel):
    """Composite record of an advanced guardrails evaluation."""

    model_config = ConfigDict(frozen=True)

    input: AdvancedGuardrailInput
    outcome: GuardrailDecisionOutcome
    reason_category: str = Field(min_length=1)
    safe_reply: str | None = Field(default=None)
    check_results: Sequence[CheckResult] = Field(default_factory=tuple)
    audit_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _blocked_has_reply(self) -> AdvancedGuardrailDecision:
        if self.outcome != GuardrailDecisionOutcome.ALLOWED and not self.safe_reply:
            raise ValueError("safe_reply is required when outcome is not ALLOWED")
        return self


class RedirectionState(BaseModel):
    """Lightweight per-conversation tracking to prevent redirection loops."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str = Field(min_length=1)
    consecutive_off_topic_count: int = Field(default=0, ge=0)
    redirection_threshold: int = Field(default=2, ge=1)
    last_safe_reply: str | None = Field(default=None)


__all__ = [
    "AdvancedGuardrailDecision",
    "AdvancedGuardrailInput",
    "CheckResult",
    "CheckVerdict",
    "ConversationContext",
    "CoverageResult",
    "CoverageStatus",
    "RedirectionState",
    "RiskPattern",
    "TrustedHealthcareCatalog",
    "TrustedHealthcareEntry",
]

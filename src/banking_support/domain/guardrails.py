"""Guardrails domain: evaluation inputs, outputs, policies, and sensitive data categories.

All models are pure data structures with no business logic or external dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field

from banking_support.domain.conversation import ConversationStatus, CustomerClassification
from banking_support.domain.routing import SupportIntent


class GuardrailDecisionOutcome(StrEnum):
    """Result of a guardrails evaluation."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FAILED = "failed"


class SensitiveDataCategory(StrEnum):
    """Categories of information that guardrails protect from exposure."""

    NAME = "name"
    PHONE_NUMBER = "phone_number"
    IBAN = "iban"
    SECRET_ANSWER = "secret_answer"
    CREDENTIAL = "credential"
    INTERNAL_PROMPT = "internal_prompt"
    API_KEY = "api_key"
    OTHER_CUSTOMER_DATA = "other_customer_data"


class GuardrailInput(BaseModel):
    """Content and trusted workflow context submitted for guardrails evaluation."""

    model_config = ConfigDict(frozen=True)

    content: str = Field(min_length=1)
    content_type: str = Field(pattern=r"^(customer_input|assistant_output)$")
    conversation_id: str = Field(min_length=1)
    status: ConversationStatus = ConversationStatus.COLLECTING
    matched_customer_id: str | None = None
    customer_classification: CustomerClassification | None = None
    support_intent: SupportIntent | None = None
    messages: Sequence[BaseMessage] = Field(default_factory=tuple)
    sensitive_values: frozenset[str] = Field(default_factory=frozenset)
    has_collected_attributes: bool = Field(
        default=False,
        description="True when the greeter has already collected some identification attributes.",
    )


class GuardrailOutput(BaseModel):
    """Result of a guardrails evaluation.

    When ``outcome`` is not ``ALLOWED``, ``safe_reply`` is required and must not
    contain PII, secrets, credentials, or internal implementation details.
    """

    model_config = ConfigDict(frozen=True)

    outcome: GuardrailDecisionOutcome
    reason_category: str = Field(min_length=1)
    safe_reply: str | None = Field(
        default=None,
        description="Customer-facing response when the evaluation is not ALLOWED.",
    )
    sanitized_content: str | None = Field(
        default=None,
        description="Content with sensitive values redacted, for safe downstream use.",
    )
    audit_metadata: dict[str, Any] = Field(default_factory=dict)


class BankingPolicyRule(BaseModel):
    """Trusted configuration rule defining permitted/prohibited banking actions."""

    model_config = ConfigDict(frozen=True)

    action_type: str = Field(min_length=1)
    allowed_tiers: frozenset[CustomerClassification] = Field(default_factory=frozenset)
    requires_authentication: bool = True
    allow_routing_as_inquiry: bool = False
    prohibited_commitments: frozenset[str] = Field(default_factory=frozenset)


class GuardrailEvaluation(BaseModel):
    """Composite record of a guardrails evaluation for audit correlation."""

    model_config = ConfigDict(frozen=True)

    input: GuardrailInput
    output: GuardrailOutput


__all__ = [
    "BankingPolicyRule",
    "GuardrailDecisionOutcome",
    "GuardrailEvaluation",
    "GuardrailInput",
    "GuardrailOutput",
    "SensitiveDataCategory",
]

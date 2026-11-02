"""Typed boundaries for the deterministic workflow node strategies.

The graph owns node names and topology; this module owns the dependency contract
used when assembling the focused strategy callables. Keeping assembly explicit
prevents a node from silently reaching for a global repository or provider.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from healthcare_support.agents.llm import LLMExtractor, SupportIntentClassifier
from healthcare_support.agents.state import GraphState
from healthcare_support.core.responses import (
    DATA_REQUEST_REFUSAL,
    INTERNAL_DISCLOSURE_REFUSAL,
    MANIPULATION_RE_PROMPT,
    PREMIUM_RESTRICTION_MESSAGE,
    PRIVACY_VIOLATION_MESSAGE,
    PROHIBITED_ACTION_MESSAGE,
    UNAVAILABLE_GUARDIAL_MESSAGE,
)
from healthcare_support.data.repository import CustomerRepository
from healthcare_support.domain.conversation import ConversationStatus, CustomerClassification
from healthcare_support.domain.guardrails import GuardrailInput, GuardrailOutput
from healthcare_support.domain.routing import SupportDirectory, SupportIntent
from healthcare_support.observability.audit import build_audit_event, emit

NodeStrategy = Callable[[GraphState], dict[str, Any]]

NODE_NAMES = (
    "guardrail",
    "extract",
    "identify",
    "authenticate",
    "classify",
    "specialist",
    "output_guardrail",
    "respond",
    "terminated",
)


@dataclass(frozen=True)
class WorkflowDependencies:
    """All external dependencies available to node strategies."""

    repository: CustomerRepository
    extractor: LLMExtractor
    default_phone_region: str
    intent_classifier: SupportIntentClassifier | None
    support_directory: SupportDirectory


def last_user_text(state: GraphState) -> str:
    """Return the raw current-turn input, falling back to checkpointed history."""
    user_input = state.get("user_input")
    if user_input:
        return str(user_input)
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def sanitized_history(state: GraphState) -> list[dict[str, str]]:
    """Return bounded role/content history without workflow state."""
    return [
        {
            "role": "user" if isinstance(message, HumanMessage) else "assistant",
            "content": str(message.content),
        }
        for message in state.get("messages", [])[-6:]
    ]


def find_customer(repository: CustomerRepository, customer_id: str | None) -> Any:
    if customer_id is None:
        return None
    for customer in repository.list_all():
        if customer.id == customer_id:
            return customer
    return None


def guardrail_messages(state: GraphState) -> list[BaseMessage]:
    """Return checkpointed history plus the current turn for guardrail checks."""
    messages = list(state.get("messages", []))
    user_input = state.get("user_input")
    if user_input:
        text = str(user_input)
        if (
            not messages
            or not isinstance(messages[-1], HumanMessage)
            or str(messages[-1].content) != text
        ):
            messages.append(HumanMessage(content=text))
    return messages


def build_guardrail_input(
    state: GraphState,
    *,
    content_type: str,
    content: str,
    sensitive_values: frozenset[str] | None = None,
) -> GuardrailInput:
    classification_value = state.get("customer_classification")
    try:
        classification = (
            CustomerClassification(classification_value)
            if classification_value is not None
            else None
        )
    except ValueError:
        classification = None

    status_value = state.get("status")
    try:
        status = ConversationStatus(status_value) if status_value else ConversationStatus.COLLECTING
    except ValueError:
        status = ConversationStatus.COLLECTING

    intent_value = state.get("support_intent")
    try:
        intent = SupportIntent(intent_value) if intent_value is not None else None
    except ValueError:
        intent = None

    return GuardrailInput(
        content=content,
        content_type=content_type,
        conversation_id=state.get("conversation_id", ""),
        status=status,
        matched_customer_id=state.get("matched_customer_id"),
        customer_classification=classification,
        support_intent=intent,
        messages=guardrail_messages(state),
        sensitive_values=sensitive_values or frozenset(),
        has_collected_attributes=any(
            state.get(key) for key in ("attr_name", "attr_phone", "attr_iban")
        ),
    )


def emit_guardrail_event(state: GraphState, decision: GuardrailOutput) -> None:
    emit(
        build_audit_event(
            event_type=f"guardrail_{decision.outcome.value}",
            conversation_id=state.get("conversation_id", ""),
            guardrail_outcome=decision.outcome.value,
            guardrail_reason=decision.reason_category,
            content_type=decision.audit_metadata.get("content_type"),
            identified=state.get("status") == ConversationStatus.AUTHENTICATED.value,
            authenticated=state.get("status") == ConversationStatus.AUTHENTICATED.value,
            identification_attempts=state.get("identification_attempts", 0),
            secret_answer_attempts=state.get("secret_answer_attempts", 0),
            classification=state.get("customer_classification"),
        )
    )


def safe_reply_for(decision: GuardrailOutput) -> str:
    if decision.safe_reply:
        return decision.safe_reply
    mapping = {
        "prompt_injection": MANIPULATION_RE_PROMPT,
        "internal_disclosure": INTERNAL_DISCLOSURE_REFUSAL,
        "unauthenticated": DATA_REQUEST_REFUSAL,
        "premium_restriction": PREMIUM_RESTRICTION_MESSAGE,
        "prohibited_financial_action": PROHIBITED_ACTION_MESSAGE,
        "privacy_violation": PRIVACY_VIOLATION_MESSAGE,
        "unauthorized_commitment": PROHIBITED_ACTION_MESSAGE,
        "check_unavailable": UNAVAILABLE_GUARDIAL_MESSAGE,
    }
    return mapping.get(decision.reason_category, MANIPULATION_RE_PROMPT)


def build_node_strategies(
    dependencies: WorkflowDependencies,
    strategies: Mapping[str, NodeStrategy],
) -> dict[str, NodeStrategy]:
    """Validate and return the named strategies used by the graph.

    This is deliberately a small assembly boundary: missing or extra node names
    fail at graph construction rather than changing topology at runtime.
    """
    del dependencies  # The mapping's closures capture the validated dependencies.
    expected = set(NODE_NAMES)
    actual = set(strategies)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"invalid workflow strategies; missing={missing}, extra={extra}")
    return dict(strategies)


__all__ = [
    "NODE_NAMES",
    "NodeStrategy",
    "WorkflowDependencies",
    "build_guardrail_input",
    "build_node_strategies",
    "emit_guardrail_event",
    "find_customer",
    "last_user_text",
    "safe_reply_for",
    "sanitized_history",
]

"""LangGraph state schema for the verification workflow.

Plain built-in types are used for enum fields so serialization through the
in-memory checkpointer is trivial and language-agnostic.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from healthcare_support.domain.conversation import ConversationStatus

CHECKPOINT_TRANSIENT_FIELDS = frozenset({"user_input", "pending_secret_answer"})


def checkpoint_safe_state(state: dict[str, Any]) -> dict[str, Any]:
    """Project state without current-turn input, secret answers, or raw user messages."""
    safe = {key: value for key, value in state.items() if key not in CHECKPOINT_TRANSIENT_FIELDS}
    messages = safe.get("messages")
    if messages is not None:
        safe["messages"] = [
            message for message in messages if getattr(message, "type", "") != "human"
        ]
    return safe


class GraphState(TypedDict):
    """Checkpointed graph state keyed by conversation_id (thread_id)."""

    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Conversation identifier (also the LangGraph thread_id).
    conversation_id: str

    # Raw user input for the current turn. Stored separately from the message
    # history so that sensitive values can be redacted before persistence.
    user_input: str | None

    # Collected identifying attributes (latest values).
    attr_name: str | None
    attr_phone: str | None
    attr_date_of_birth: str | None

    # Workflow state.
    status: str  # ConversationStatus values
    matched_patient_id: str | None
    identification_attempts: int
    secret_answer_attempts: int
    terminated: bool
    termination_reason: str | None  # TerminationReason values

    # Routing support.
    extraction_intent: str | None  # ExtractionIntent values

    # Outputs produced by nodes.
    reply: str | None
    pending_secret_answer: str | None

    # History management metadata (e.g., truncation counters), kept separate from
    # the message list so that trusted workflow state is not affected.
    history_metadata: dict[str, Any] | None

    # Guardrails decision for the current turn (serialized dict for checkpointer compatibility).
    guardrail_decision: dict[str, Any] | None

    # Classification result produced by the Bouncer Agent after authentication.
    patient_classification: str | None  # PatientClassification values

    # Specialist routing outputs (sanitized — no PII or secrets).
    support_intent: str | None  # SupportIntent values
    support_specialization: str | None
    routing_status: str | None  # RoutingStatus values
    support_department: str | None
    routing_contact: str | None


def make_initial_state(conversation_id: str) -> dict[str, Any]:
    """Return the default state for a brand-new conversation."""
    return {
        "messages": [],
        "conversation_id": conversation_id,
        "user_input": None,
        "attr_name": None,
        "attr_phone": None,
        "attr_date_of_birth": None,
        "status": ConversationStatus.COLLECTING.value,
        "matched_patient_id": None,
        "identification_attempts": 0,
        "secret_answer_attempts": 0,
        "terminated": False,
        "termination_reason": None,
        "extraction_intent": None,
        "reply": None,
        "pending_secret_answer": None,
        "history_metadata": None,
        "guardrail_decision": None,
        "patient_classification": None,
        "support_intent": None,
        "support_specialization": None,
        "routing_status": None,
        "support_department": None,
        "routing_contact": None,
    }

"""Audit events for identification/authentication workflow transitions.

Audit events contain outcomes and counters only — never attribute values or secret
answers.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

logger = logging.getLogger("healthcare_support.audit")

# Audit is an allowlist, not a general-purpose state serializer. Raw content,
# credentials, and customer attributes have no representable fields.
SAFE_AUDIT_FIELDS = frozenset(
    {
        "identified",
        "authenticated",
        "terminated",
        "termination_reason",
        "identification_attempts",
        "secret_answer_attempts",
        "classification",
        "routing_status",
        "routing_intent",
        "department_key",
        "guardrail_outcome",
        "guardrail_reason",
        "content_type",
        "access_outcome",
        "access_reason",
    }
)


@dataclasses.dataclass(frozen=True)
class AuditEvent:
    """Immutable audit event."""

    event_type: str
    conversation_id: str
    identified: bool = False
    authenticated: bool = False
    terminated: bool = False
    termination_reason: str | None = None
    identification_attempts: int = 0
    secret_answer_attempts: int = 0
    classification: str | None = None
    routing_status: str | None = None
    routing_intent: str | None = None
    department_key: str | None = None
    guardrail_outcome: str | None = None
    guardrail_reason: str | None = None
    content_type: str | None = None
    access_outcome: str | None = None
    access_reason: str | None = None


def build_audit_event(
    event_type: str | None = None,
    conversation_id: str | None = None,
    **fields: Any,
) -> AuditEvent:
    """Build an audit event using only the explicit redaction-safe allowlist."""
    if event_type is None or conversation_id is None:
        raise TypeError("event_type and conversation_id are required")
    safe_fields = {key: value for key, value in fields.items() if key in SAFE_AUDIT_FIELDS}
    return AuditEvent(event_type=event_type, conversation_id=conversation_id, **safe_fields)


def emit(event: AuditEvent) -> None:
    """Emit a structured audit event."""
    logger.info("%s", dataclasses.asdict(event))


__all__ = ["AuditEvent", "SAFE_AUDIT_FIELDS", "build_audit_event", "emit"]

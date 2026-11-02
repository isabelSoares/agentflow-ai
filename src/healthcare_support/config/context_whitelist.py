"""Patterns for workflow-necessary messages that should not be blocked.

These patterns keep the fixed, non-disclosing response templates in
``healthcare_support.core.responses`` from being rejected by the output
guardrail's relevance check. They intentionally describe workflow wording
(verification, routing, refusals) and never customer record data.
"""

from __future__ import annotations

WORKFLOW_MESSAGE_PATTERNS: tuple[str, ...] = (
    r"\b(phone\s+number|secret\s+question|security\s+question|your\s+name|your\s+date\s+of\s+birth|"
    r"dates?\s+of\s+birth|dob\b|verif\w*|identity\s+has\s+been|department|specialist|routing|routed|clarify)\b",
    r"\b(thank\s+you|please\s+provide|please\s+try\s+again|doesn't\s+match\s+our\s+records|"
    r"not\s+able\s+to|wasn't\s+able\s+to|didn't\s+catch|identity|session\s+has\s+ended)\b",
    r"\b(premium|regular|non[-\s]?customer|existing\s+customers|"
    r"branch|contact\s+your\s+bank|support\s+department)\b",
)

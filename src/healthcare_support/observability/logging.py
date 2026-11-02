"""Structured logging with PII redaction."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

# Very conservative patterns: redact IBAN-like tokens and phone-like tokens from
# any logged string. The real protection is architectural (we do not put PII in
# log messages); this is a defense-in-depth belt-and-suspenders filter.
_REDACTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}\b"),
    re.compile(r"\+\d[\d\s\-]{6,20}"),
    re.compile(r"\b(?:gsk_|sk-)[A-Za-z0-9_\-]{8,}\b"),
]


class _JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        if hasattr(record, "conversation_id"):
            payload["conversation_id"] = record.conversation_id
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        return json.dumps(payload, default=str)


def redact(text: str) -> str:
    """Return `text` with IBAN/phone-like tokens replaced."""
    for pattern in _REDACTION_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON output and redaction."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]

    # Audit logger inherits the same handler; events are emitted via `audit.emit()`.
    logging.getLogger("healthcare_support.audit").setLevel(logging.INFO)

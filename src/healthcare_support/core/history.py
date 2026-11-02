"""Conversation history manipulation helpers.

These functions are pure business logic: they know how to turn a list of
LangGraph messages into a sanitized, bounded, redacted history view, but they
know nothing about where the history is stored.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def sanitize_history(
    messages: Sequence[BaseMessage],
    max_messages: int | None = None,
) -> list[dict[str, str]]:
    """Return recent role/content pairs for LLM context.

    Only ``HumanMessage`` and ``AIMessage`` are included; system and tool
    messages are dropped to avoid leaking internal state.
    """
    history: list[dict[str, str]] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            continue
        history.append({"role": role, "content": str(message.content)})
    if max_messages is not None:
        history = truncate_history(history, max_messages)
    return history


def truncate_history(history: list[dict[str, str]], max_messages: int) -> list[dict[str, str]]:
    """Return at most ``max_messages`` most recent entries.

    The limit is applied to the sanitized view; the underlying graph state is
    not modified. Trusted workflow state lives outside the message list and is
    unaffected by truncation.
    """
    if max_messages <= 0:
        return []
    return history[-max_messages:]


def _compile_redaction_pattern(values: set[str]) -> re.Pattern[str] | None:
    """Build a case-insensitive regex that matches any of the given values.

    Values are sorted by length descending so that longer matches take
    precedence over shorter substrings.
    """
    cleaned = {value.strip() for value in values if value and value.strip()}
    if not cleaned:
        return None
    escaped = [re.escape(value) for value in sorted(cleaned, key=len, reverse=True)]
    return re.compile("|".join(escaped), re.IGNORECASE)


def redact_sensitive_values(text: str, sensitive_values: set[str]) -> str:
    """Replace known sensitive values with ``[REDACTED]``.

    The function does not attempt to infer sensitivity from context; it only
    redacts exact matches for the supplied values. Pattern-based redaction for
    IBANs and phone numbers is handled separately.
    """
    pattern = _compile_redaction_pattern(sensitive_values)
    if pattern is None:
        return text
    return pattern.sub("[REDACTED]", text)


def _redact_patterns(text: str) -> str:
    """Redact IBAN-like and phone-number-like substrings."""
    # IBAN: two letters followed by up to 30 alphanumeric characters, allowing
    # optional spaces every four characters.
    iban_pattern = re.compile(
        r"[A-Z]{2}\d{2}(?:\s?[A-Z0-9]){11,30}",
        re.IGNORECASE,
    )
    # E.164-ish phone number: optional leading +, digits with optional
    # separators (spaces, dashes, parentheses).
    phone_pattern = re.compile(
        r"(?:\+?\d[\d\s\-\(\)]{7,}\d)",
    )
    text = iban_pattern.sub("[REDACTED]", text)
    return phone_pattern.sub("[REDACTED]", text)


def redact_message(
    text: str,
    sensitive_values: set[str] | None = None,
    enable_patterns: bool = True,
) -> str:
    """Redact a message before persistence.

    Applies known-value redaction first, then pattern-based redaction for
    IBANs and phone numbers.
    """
    redacted = redact_sensitive_values(text, sensitive_values or set())
    if enable_patterns:
        redacted = _redact_patterns(redacted)
    return redacted


__all__ = [
    "sanitize_history",
    "truncate_history",
    "redact_sensitive_values",
    "redact_message",
]

"""Sensitive-topic whitelist for legitimate banking support requests.

Messages matching these patterns should not be blocked as harmful simply because
they mention fraud, scams, or account security.
"""

from __future__ import annotations

SENSITIVE_TOPIC_PATTERNS: tuple[str, ...] = (
    r"\b(fraud|fraudulent|unauthorized\s+transaction|suspicious\s+transaction|"
    r"account\s+security|report\s+(fraud|scam)|stolen\s+card)\b",
)

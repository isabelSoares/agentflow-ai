"""Sensitive-topic whitelist for legitimate healthcare support requests.

Messages matching these patterns should not be blocked as harmful simply because
they mention fraud, scams, or patient portal security.
"""

from __future__ import annotations

SENSITIVE_TOPIC_PATTERNS: tuple[str, ...] = (
    r"\b(fraud|fraudulent|unauthorized\s+(claim|charge)|suspicious\s+(claim|charge)|"
    r"medical\s+identity\s+theft|insurance\s+fraud|billing\s+fraud|"
    r"portal\s+security|report\s+(fraud|scam)|stolen\s+(insurance\s+card|medical\s+id|card))\b",
)

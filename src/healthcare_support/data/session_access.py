"""In-memory session ownership store.

A conversation identifier is a public routing value and MUST NOT authorize a
session on its own. When a conversation is created, the application issues an
opaque ownership proof; only its SHA-256 digest is retained here and compared in
constant time. The raw proof is returned to the caller once and never stored,
logged, or placed in conversation history.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

PROOF_HEADER = "X-Session-Proof"

# token_urlsafe(32) yields a long opaque token; anything this short is malformed.
_MIN_PROOF_LENGTH = 16
_DIGEST_PATTERN = r"^[0-9a-f]{64}$"


class AccessDecision(StrEnum):
    """Outcome of a session access check. Every non-granted value maps to 401."""

    GRANTED = "granted"
    MISSING = "missing"
    MALFORMED = "malformed"
    UNKNOWN = "unknown"
    INVALID = "invalid"
    INACTIVE = "inactive"


class SessionOwnershipRecord(BaseModel):
    """Authoritative ownership record for a single conversation."""

    model_config = ConfigDict(frozen=True)

    conversation_id: str = Field(min_length=1)
    proof_digest: str = Field(pattern=_DIGEST_PATTERN)
    created_at: datetime
    active: bool = True

    @field_validator("created_at")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class SessionAccessStore:
    """Deterministic, in-memory session ownership store.

    Performs no I/O and uses only the standard library. Records live for the
    process lifetime and are cleared on application restart, matching the
    existing in-memory graph/history stores.
    """

    def __init__(self) -> None:
        self._records: dict[str, SessionOwnershipRecord] = {}

    @staticmethod
    def _digest(proof: str) -> str:
        return hashlib.sha256(proof.encode("utf-8")).hexdigest()

    def create(self, conversation_id: str) -> str:
        """Create a session record and return the raw proof exactly once."""
        if not conversation_id:
            raise ValueError("conversation_id must be non-empty")
        existing = self._records.get(conversation_id)
        if existing is not None and existing.active:
            raise ValueError("conversation already has an active session")
        proof = secrets.token_urlsafe(32)
        self._records[conversation_id] = SessionOwnershipRecord(
            conversation_id=conversation_id,
            proof_digest=self._digest(proof),
            created_at=datetime.now(UTC),
            active=True,
        )
        return proof

    def verify(self, conversation_id: str, presented_proof: str | None) -> AccessDecision:
        """Return the access decision for the presented proof."""
        candidate = presented_proof if presented_proof is not None else ""
        candidate_digest = self._digest(candidate)
        record = self._records.get(conversation_id)

        if record is None:
            # Compare anyway so a missing record is not distinguishable by timing.
            hmac.compare_digest(candidate_digest, candidate_digest)
            return AccessDecision.UNKNOWN

        if presented_proof is None:
            return AccessDecision.MISSING
        if len(presented_proof) < _MIN_PROOF_LENGTH:
            return AccessDecision.MALFORMED
        if not hmac.compare_digest(candidate_digest, record.proof_digest):
            return AccessDecision.INVALID
        if not record.active:
            return AccessDecision.INACTIVE
        return AccessDecision.GRANTED

    def rotate(self, conversation_id: str) -> str:
        """Replace the proof for an existing session and return the new raw proof."""
        record = self._records.get(conversation_id)
        if record is None:
            raise KeyError(conversation_id)
        proof = secrets.token_urlsafe(32)
        self._records[conversation_id] = SessionOwnershipRecord(
            conversation_id=conversation_id,
            proof_digest=self._digest(proof),
            created_at=datetime.now(UTC),
            active=True,
        )
        return proof

    def deactivate(self, conversation_id: str) -> None:
        """Mark a session inactive so later requests are denied."""
        record = self._records.get(conversation_id)
        if record is None:
            return
        self._records[conversation_id] = record.model_copy(update={"active": False})

    def is_active(self, conversation_id: str) -> bool:
        record = self._records.get(conversation_id)
        return record is not None and record.active

    def clear(self) -> None:
        """Remove all records (test helper)."""
        self._records.clear()


__all__ = [
    "AccessDecision",
    "PROOF_HEADER",
    "SessionAccessStore",
    "SessionOwnershipRecord",
]

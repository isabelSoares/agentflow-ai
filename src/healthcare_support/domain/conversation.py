"""Conversation domain: attributes, status enums, and extraction intent."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ConversationStatus(StrEnum):
    COLLECTING = "collecting"
    IDENTIFIED = "identified"
    AUTHENTICATED = "authenticated"
    TERMINATED = "terminated"


class TerminationReason(StrEnum):
    IDENTIFICATION_EXHAUSTED = "identification_exhausted"
    SECRET_EXHAUSTED = "secret_exhausted"


class CustomerClassification(StrEnum):
    """Deterministic classification produced by the Bouncer Agent."""

    PREMIUM = "premium"
    REGULAR = "regular"
    NON_CUSTOMER = "non_customer"


class ExtractionIntent(StrEnum):
    """Intents produced by the LLM extractor.

    EMPTY and MANIPULATIVE inputs are handled by the deterministic input guardrail
    *before* extraction (constitution Principle II). The LLM intent is used only for
    non-security routing.
    """

    PROVIDE_IDENTIFICATION = "provide_identification"
    ANSWER_SECRET = "answer_secret"
    REQUEST_DATA = "request_data"
    CHITCHAT = "chitchat"


class ProvidedAttributes(BaseModel):
    """Attributes collected from the caller during a conversation."""

    name: str | None = None
    phone: str | None = None
    iban: str | None = None

    def update(self, other: ProvidedAttributes) -> ProvidedAttributes:
        """Return a new instance with the latest non-None values."""
        return ProvidedAttributes(
            name=other.name if other.name is not None else self.name,
            phone=other.phone if other.phone is not None else self.phone,
            iban=other.iban if other.iban is not None else self.iban,
        )

    def is_empty(self) -> bool:
        return self.name is None and self.phone is None and self.iban is None

    def provided_count(self) -> int:
        return sum(1 for v in (self.name, self.phone, self.iban) if v is not None)

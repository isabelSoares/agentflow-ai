"""Domain models for customers and conversations.

PII/secret fields exist only inside domain objects; they are never serialized to API
responses or logs.
"""

from __future__ import annotations

from datetime import date

import phonenumbers
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Customer(BaseModel):
    """A registered customer. `secret_answer` is NEVER logged."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    phone: str  # E.164 format, validated below
    date_of_birth: str  # ISO date (YYYY-MM-DD), validated below
    secret_question: str = Field(min_length=1)
    secret_answer: str = Field(min_length=1)
    is_premium: bool = False

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: str) -> str:
        try:
            parsed = phonenumbers.parse(value, None)
        except phonenumbers.NumberParseException as exc:
            raise ValueError(f"Invalid phone number: {exc}") from exc
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_date_of_birth(cls, value: str) -> str:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError("Invalid date of birth; expected YYYY-MM-DD") from exc

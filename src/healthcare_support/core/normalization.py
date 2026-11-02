"""Attribute normalization for deterministic comparison.

This module imports no LLM or web dependencies; it is a pure dependency of the
verification core.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

import phonenumbers


def normalize_name(name: str | None) -> str | None:
    """Return the canonical name representation used by every identity flow."""
    if not name:
        return None
    name = "".join(
        character
        for character in unicodedata.normalize("NFKD", name.casefold())
        if not unicodedata.combining(character)
    )
    name = name.strip()
    if not name:
        return None
    return " ".join(name.split())


def name_parts_match(provided: str | None, registered: str) -> bool:
    """True if the provided name equals the full registered name or one of its parts.

    "Lisa" matches a registered name of "Lisa" or "Lisa Smith"; "Lisa Smith"
    matches "Lisa Smith" but not "Lisa" alone.
    """
    provided_norm = normalize_name(provided)
    if provided_norm is None:
        return False
    registered_norm = normalize_name(registered)
    assert registered_norm is not None
    if provided_norm == registered_norm:
        return True
    registered_parts = set(registered_norm.split())
    provided_parts = set(provided_norm.split())
    # Provided must be a single token that appears as a part of the registered name.
    return len(provided_parts) == 1 and provided_parts <= registered_parts


def normalize_phone(phone: str | None, default_region: str = "DE") -> str | None:
    """Return E.164 format or None if the number cannot be parsed/validated."""
    if not phone:
        return None
    try:
        parsed = phonenumbers.parse(phone, default_region)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


_DATE_OF_BIRTH_PATTERN = re.compile(r"^\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s*$")


def normalize_date_of_birth(value: str | None) -> str | None:
    """Return an ISO date (YYYY-MM-DD) or None if the value is invalid."""
    if not value:
        return None
    match = _DATE_OF_BIRTH_PATTERN.match(value)
    if match is None:
        return None
    try:
        parsed = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None
    return parsed.isoformat()


def normalize_answer(answer: str | None) -> str | None:
    """Case-fold and trim whitespace for secret-answer comparison."""
    if answer is None:
        return None
    answer = answer.strip().casefold()
    return answer if answer else None

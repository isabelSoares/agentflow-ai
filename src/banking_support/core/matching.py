"""Deterministic customer identification by 2-of-3 attribute matching."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from banking_support.core.normalization import (
    name_parts_match,
    normalize_iban,
    normalize_name,
    normalize_phone,
)
from banking_support.data.repository import CustomerRepository
from banking_support.domain.conversation import ProvidedAttributes
from banking_support.domain.customer import Customer


class MatchOutcome(StrEnum):
    UNIQUE = "unique"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class MatchResult:
    outcome: MatchOutcome
    customers: Sequence[Customer]
    evaluated_attributes: int


def evaluate_match(
    attributes: ProvidedAttributes,
    repository: CustomerRepository,
    default_phone_region: str = "DE",
) -> MatchResult:
    """Evaluate provided attributes against the customer repository.

    - If fewer than 2 attributes are present: INSUFFICIENT_DATA.
    - If exactly one record matches at least 2 of the provided attributes: UNIQUE.
    - If multiple records match at least 2 attributes: AMBIGUOUS.
    - If no records match at least 2 attributes: NO_MATCH.

    An ambiguous match is NOT a failure and does NOT consume an identification
    attempt (spec FR-005).
    """
    norm_name = normalize_name(attributes.name)
    norm_phone = normalize_phone(attributes.phone, default_phone_region)
    norm_iban = normalize_iban(attributes.iban)

    evaluated = sum(1 for v in (norm_name, norm_phone, norm_iban) if v is not None)
    if evaluated < 2:
        return MatchResult(MatchOutcome.INSUFFICIENT_DATA, [], evaluated)

    matches: list[Customer] = []
    for customer in repository.list_all():
        score = 0
        if norm_name is not None and name_parts_match(norm_name, customer.name):
            score += 1
        if norm_phone is not None and normalize_phone(customer.phone) == norm_phone:
            score += 1
        if norm_iban is not None and normalize_iban(customer.iban) == norm_iban:
            score += 1
        if score >= 2:
            matches.append(customer)

    if len(matches) == 1:
        return MatchResult(MatchOutcome.UNIQUE, matches, evaluated)
    if len(matches) > 1:
        return MatchResult(MatchOutcome.AMBIGUOUS, matches, evaluated)
    return MatchResult(MatchOutcome.NO_MATCH, [], evaluated)


# Re-export for consumers that only need normalization through matching.
__all__ = ["evaluate_match", "MatchOutcome", "MatchResult"]

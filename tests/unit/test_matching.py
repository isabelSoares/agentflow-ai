"""Unit tests for deterministic customer matching (FR-002, FR-004, FR-005, FR-006)."""

from __future__ import annotations

import pytest

from banking_support.core.matching import MatchOutcome, evaluate_match
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.seed import CUSTOMERS
from banking_support.domain.conversation import ProvidedAttributes


@pytest.fixture
def repository() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository(CUSTOMERS)


class TestUniqueMatches:
    def test_name_and_phone(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(name="Lisa", phone="+14155552671")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE
        assert result.customers[0].name == "Lisa"

    def test_name_and_iban(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(name="Lisa", iban="DE89370400440532013000")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE

    def test_phone_and_iban(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(phone="+14155552671", iban="DE89370400440532013000")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE

    def test_all_three(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(
            name="Lisa",
            phone="+14155552671",
            iban="DE89370400440532013000",
        )
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE

    def test_formatting_variants(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(
            name="lisa",
            phone="+1 415 555 2671",
            iban="de89 3704 0044 0532 0130 00",
        )
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE


class TestNoMatch:
    def test_single_attribute(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(name="Lisa")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.INSUFFICIENT_DATA

    def test_no_record(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(name="Nobody", phone="+14155550000")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.NO_MATCH
        assert result.evaluated_attributes == 2


class TestAmbiguousMatch:
    def test_two_customers_same_name_and_phone(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        attrs = ProvidedAttributes(name="Maria", phone="+351912345678")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.AMBIGUOUS
        assert len(result.customers) == 2

    def test_ambiguous_does_not_consume_attempt(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        # Ambiguity is not a failure; attempt counter must be unchanged.
        attrs = ProvidedAttributes(name="Maria", phone="+351912345678")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.AMBIGUOUS


class TestReEvaluation:
    def test_update_attribute_re_evaluates(self, repository: InMemoryCustomerRepository) -> None:
        attrs = ProvidedAttributes(name="Maria", phone="+351912345678")
        ambiguous = evaluate_match(attrs, repository, default_phone_region="DE")
        assert ambiguous.outcome == MatchOutcome.AMBIGUOUS

        updated = ProvidedAttributes(
            name="Maria Silva",
            phone="+351912345678",
            iban="PT50000201230000000001087",
        )
        resolved = evaluate_match(updated, repository, default_phone_region="DE")
        assert resolved.outcome == MatchOutcome.UNIQUE
        assert resolved.customers[0].name == "Maria Silva"

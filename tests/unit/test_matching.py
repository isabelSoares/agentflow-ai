"""Unit tests for deterministic patient matching (FR-002, FR-004, FR-005, FR-006)."""

from __future__ import annotations

import pytest

from healthcare_support.core.matching import MatchOutcome, evaluate_match
from healthcare_support.data.memory import InMemoryPatientRepository
from healthcare_support.data.seed import PATIENTS
from healthcare_support.domain.conversation import ProvidedAttributes


@pytest.fixture
def repository() -> InMemoryPatientRepository:
    return InMemoryPatientRepository(PATIENTS)


class TestUniqueMatches:
    def test_name_and_phone(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(name="Lisa", phone="+14155552671")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE
        assert result.patients[0].name == "Lisa"

    def test_name_and_date_of_birth(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(name="Lisa", date_of_birth="1990-01-15")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE

    def test_phone_and_date_of_birth(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(phone="+14155552671", date_of_birth="1990-01-15")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE

    def test_all_three(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(
            name="Lisa",
            phone="+14155552671",
            date_of_birth="1990-01-15",
        )
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE

    def test_formatting_variants(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(
            name="lisa",
            phone="+1 415 555 2671",
            date_of_birth="1990-1-15",
        )
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.UNIQUE


class TestNoMatch:
    def test_single_attribute(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(name="Lisa")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.INSUFFICIENT_DATA

    def test_no_record(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(name="Nobody", phone="+14155550000")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.NO_MATCH
        assert result.evaluated_attributes == 2


class TestAmbiguousMatch:
    def test_two_patients_same_name_and_phone(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(name="Maria", phone="+351912345678")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.AMBIGUOUS
        assert len(result.patients) == 2

    def test_ambiguous_does_not_consume_attempt(
        self, repository: InMemoryPatientRepository
    ) -> None:
        # Ambiguity is not a failure; attempt counter must be unchanged.
        attrs = ProvidedAttributes(name="Maria", phone="+351912345678")
        result = evaluate_match(attrs, repository, default_phone_region="DE")
        assert result.outcome == MatchOutcome.AMBIGUOUS


class TestReEvaluation:
    def test_update_attribute_re_evaluates(self, repository: InMemoryPatientRepository) -> None:
        attrs = ProvidedAttributes(name="Maria", phone="+351912345678")
        ambiguous = evaluate_match(attrs, repository, default_phone_region="DE")
        assert ambiguous.outcome == MatchOutcome.AMBIGUOUS

        updated = ProvidedAttributes(
            name="Maria Silva",
            phone="+351912345678",
            date_of_birth="1985-07-22",
        )
        resolved = evaluate_match(updated, repository, default_phone_region="DE")
        assert resolved.outcome == MatchOutcome.UNIQUE
        assert resolved.patients[0].name == "Maria Silva"

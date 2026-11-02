"""Unit tests for attribute normalization (FR-003)."""

from __future__ import annotations

from healthcare_support.core.normalization import (
    name_parts_match,
    normalize_answer,
    normalize_iban,
    normalize_name,
    normalize_phone,
)


class TestNameNormalization:
    def test_casefold(self) -> None:
        assert normalize_name("  Lisa  ") == "lisa"

    def test_collapse_whitespace(self) -> None:
        assert normalize_name("Lisa   Smith") == "lisa smith"

    def test_unicode_whitespace_and_accents_are_canonical(self) -> None:
        assert normalize_name("  Jos\u00e9\u2003da Silva  ") == "jose da silva"

    def test_full_name_match(self) -> None:
        assert name_parts_match("Lisa Smith", "Lisa Smith") is True

    def test_first_name_part_match(self) -> None:
        assert name_parts_match("Lisa", "Lisa Smith") is True

    def test_partial_name_no_match_when_not_part(self) -> None:
        assert name_parts_match("Smith", "Lisa Doe") is False

    def test_multi_token_must_match_exactly(self) -> None:
        assert name_parts_match("Lisa Doe", "Lisa Smith") is False


class TestPhoneNormalization:
    def test_e164_with_plus(self) -> None:
        assert normalize_phone("+49 89 1234 5678", default_region="DE") == "+498912345678"

    def test_country_code_double_zero(self) -> None:
        assert normalize_phone("00498912345678", default_region="DE") == "+498912345678"

    def test_spaces_and_dashes_ignored(self) -> None:
        assert normalize_phone("+1 (415) 555-2671", default_region="US") == "+14155552671"

    def test_invalid_returns_none(self) -> None:
        assert normalize_phone("not-a-number", default_region="DE") is None

    def test_us_number_default_region_de_still_works_with_country_code(self) -> None:
        assert normalize_phone("+14155552671", default_region="DE") == "+14155552671"


class TestIbanNormalization:
    def test_spaces_removed(self) -> None:
        assert normalize_iban("DE89 3704 0044 0532 0130 00") == "DE89370400440532013000"

    def test_lowercased(self) -> None:
        assert normalize_iban("de89370400440532013000") == "DE89370400440532013000"

    def test_invalid_returns_none(self) -> None:
        assert normalize_iban("DE00XXXX") is None


class TestAnswerNormalization:
    def test_case_and_whitespace(self) -> None:
        assert normalize_answer("  Yoda  ") == "yoda"

    def test_none(self) -> None:
        assert normalize_answer(None) is None

"""Unit tests for secret-answer verification and attempt limits (FR-008..FR-011)."""

from __future__ import annotations

import pytest

from banking_support.agents.llm import ScriptedFakeExtractor
from banking_support.agents.nodes import make_nodes
from banking_support.agents.state import make_initial_state
from banking_support.core.responses import DATA_REQUEST_REFUSAL
from banking_support.core.verification import (
    MAX_ATTEMPTS,
    check_secret_answer,
    process_identification_failure,
    process_secret_attempt,
)
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.seed import CUSTOMERS
from banking_support.domain.conversation import (
    ConversationStatus,
    ExtractionIntent,
    TerminationReason,
)
from banking_support.domain.customer import Customer


@pytest.fixture
def lisa() -> Customer:
    return CUSTOMERS[0]


@pytest.fixture
def authenticate():
    """Return the ``authenticate_node`` callable under test."""
    nodes = make_nodes(InMemoryCustomerRepository(CUSTOMERS), ScriptedFakeExtractor())
    return nodes["authenticate"]


def identified_state(**overrides):
    state = make_initial_state("unit-auth")
    state.update(
        {
            "status": ConversationStatus.IDENTIFIED.value,
            "matched_customer_id": CUSTOMERS[0].id,
            "attr_name": CUSTOMERS[0].name,
            "attr_phone": CUSTOMERS[0].phone,
        }
    )
    state.update(overrides)
    return state


class TestCheckSecretAnswer:
    def test_exact_match(self, lisa: Customer) -> None:
        assert check_secret_answer("Yoda", lisa) is True

    def test_case_insensitive(self, lisa: Customer) -> None:
        assert check_secret_answer("yoda", lisa) is True

    def test_whitespace_trimmed(self, lisa: Customer) -> None:
        assert check_secret_answer("  Yoda  ", lisa) is True

    def test_wrong_answer(self, lisa: Customer) -> None:
        assert check_secret_answer("Vader", lisa) is False


class TestProcessSecretAttempt:
    def test_correct_answer_authenticates(self, lisa: Customer) -> None:
        result = process_secret_attempt("Yoda", lisa, attempts_so_far=0)
        assert result.authenticated is True
        assert result.terminated is False

    def test_wrong_answer_retries(self, lisa: Customer) -> None:
        result = process_secret_attempt("Vader", lisa, attempts_so_far=0)
        assert result.authenticated is False
        assert result.terminated is False
        assert "try again" in result.reply.lower()

    def test_third_wrong_terminates(self, lisa: Customer) -> None:
        result = process_secret_attempt("Vader", lisa, attempts_so_far=MAX_ATTEMPTS - 1)
        assert result.authenticated is False
        assert result.terminated is True
        assert result.termination_reason == TerminationReason.SECRET_EXHAUSTED.value

    def test_correct_on_third_attempt_succeeds(self, lisa: Customer) -> None:
        result = process_secret_attempt("Yoda", lisa, attempts_so_far=MAX_ATTEMPTS - 1)
        assert result.authenticated is True
        assert result.terminated is False


class TestProcessIdentificationFailure:
    def test_failed_attempt_before_limit(self) -> None:
        result = process_identification_failure(attempts_so_far=0)
        assert result.terminated is False

    def test_third_failed_identification_terminates_non_client(self) -> None:
        result = process_identification_failure(attempts_so_far=MAX_ATTEMPTS - 1)
        assert result.terminated is True
        assert result.termination_reason == TerminationReason.IDENTIFICATION_EXHAUSTED.value
        assert "not currently a client" in result.reply


class TestAuthenticateNodePrecedence:
    """E2: a usable secret answer is verified regardless of the extraction label."""

    def test_correct_answer_with_request_data_label_authenticates(self, authenticate) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.REQUEST_DATA.value,
                pending_secret_answer="Yoda",
            )
        )
        assert result.get("status") == ConversationStatus.AUTHENTICATED.value

    def test_correct_answer_with_chitchat_label_authenticates(self, authenticate) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.CHITCHAT.value,
                pending_secret_answer="Yoda",
            )
        )
        assert result.get("status") == ConversationStatus.AUTHENTICATED.value

    def test_request_data_without_answer_still_refuses(self, authenticate) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.REQUEST_DATA.value,
                pending_secret_answer=None,
            )
        )
        assert result.get("status") is None
        assert result["reply"] == DATA_REQUEST_REFUSAL

    def test_wrong_answer_stays_unauthenticated_and_counts_attempt(self, authenticate) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.ANSWER_SECRET.value,
                pending_secret_answer="Vader",
            )
        )
        assert result.get("status") is None
        assert result["secret_answer_attempts"] == 1

    def test_answer_before_identification_does_not_authenticate(self, authenticate) -> None:
        state = identified_state(
            status=ConversationStatus.COLLECTING.value,
            extraction_intent=ExtractionIntent.ANSWER_SECRET.value,
            pending_secret_answer="Yoda",
        )
        state["matched_customer_id"] = None
        result = authenticate(state)
        assert result.get("status") is None

    def test_missing_answer_with_answer_secret_reasks(self, authenticate) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.ANSWER_SECRET.value,
                pending_secret_answer=None,
            )
        )
        assert result.get("status") is None
        assert CUSTOMERS[0].secret_question in result["reply"]


_WRONG_ANSWERS = [
    "Darth",
    "luke",
    "123",
    "null",
    "none",
    "yes",
    "no",
    "maybe",
    "a",
    "b",
    "aaaa",
    "wrong",
    "leia",
    "obiwan",
    "skywalker",
    "chewbacca",
    "han",
    "r2d2",
    "c3po",
    "test",
]


class TestNoFalseAuthentication:
    """SC-003: malformed, ambiguous, wrong, or missing answers never authenticate."""

    @pytest.mark.parametrize("answer", _WRONG_ANSWERS)
    def test_wrong_answer_never_authenticates(self, authenticate, answer: str) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.ANSWER_SECRET.value,
                pending_secret_answer=answer,
            )
        )
        assert result.get("status") != ConversationStatus.AUTHENTICATED.value

    @pytest.mark.parametrize(
        "intent",
        [
            ExtractionIntent.REQUEST_DATA.value,
            ExtractionIntent.CHITCHAT.value,
            ExtractionIntent.PROVIDE_IDENTIFICATION.value,
            ExtractionIntent.ANSWER_SECRET.value,
        ],
    )
    @pytest.mark.parametrize("answer", [None, "", "   "])
    def test_missing_or_blank_answer_never_authenticates(
        self, authenticate, intent: str, answer
    ) -> None:
        result = authenticate(
            identified_state(extraction_intent=intent, pending_secret_answer=answer)
        )
        assert result.get("status") != ConversationStatus.AUTHENTICATED.value

    def test_extraction_failure_without_answer_never_authenticates(self, authenticate) -> None:
        result = authenticate(
            identified_state(
                extraction_intent=ExtractionIntent.CHITCHAT.value,
                pending_secret_answer=None,
            )
        )
        assert result.get("status") != ConversationStatus.AUTHENTICATED.value

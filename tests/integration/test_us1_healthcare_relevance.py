"""Integration tests for User Story 1: topic relevance and redirection."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from healthcare_support.agents.graph import build_verification_graph
from healthcare_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    IntentClassification,
    LLMExtractor,
    ScriptedFakeSupportIntentClassifier,
    SupportIntent,
    SupportIntentClassifier,
)
from healthcare_support.agents.state import make_initial_state
from healthcare_support.data.memory import InMemoryPatientRepository
from healthcare_support.data.seed import PATIENTS


class _PermissiveFakeExtractor(LLMExtractor):
    """Extracts attribute-shaped text from user messages for testing."""

    def extract(
        self,
        user_text: str,
        history: list[dict[str, str]] | None = None,
    ) -> ExtractionResult:
        lowered = user_text.lower()
        import re as _re

        name = None
        name_match = _re.search(r"(?:i am|my name is)\s+([a-z]+(?:\s+[a-z]+)?)", lowered)
        if name_match:
            name = name_match.group(1).strip().title()

        phone = None
        phone_match = _re.search(r"(\+\d[\d\s-]{7,20})", user_text)
        if phone_match:
            phone = phone_match.group(1).replace(" ", "").replace("-", "")

        date_of_birth = None
        date_of_birth_match = _re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", user_text)
        if date_of_birth_match:
            date_of_birth = date_of_birth_match.group(1)

        if any([name, phone, date_of_birth]):
            intent = ExtractionIntent.PROVIDE_IDENTIFICATION
        else:
            intent = ExtractionIntent.CHITCHAT

        return ExtractionResult(intent=intent, name=name, phone=phone, date_of_birth=date_of_birth)


def _fake_intent_classifier() -> SupportIntentClassifier:
    return ScriptedFakeSupportIntentClassifier(
        script=[
            IntentClassification(
                intent=SupportIntent.SPECIALIST_REFERRAL,
                specialization="marine",
            ),
            IntentClassification(
                intent=SupportIntent.APPOINTMENT_ASSISTANCE,
                specialization=None,
            ),
        ]
    )


@pytest.fixture
def repository() -> InMemoryPatientRepository:
    return InMemoryPatientRepository(PATIENTS)


@pytest.fixture
def graph(repository: InMemoryPatientRepository):
    return build_verification_graph(
        repository,
        _PermissiveFakeExtractor(),
        default_phone_region="DE",
        intent_classifier=_fake_intent_classifier(),
    )


def _run(graph, conversation_id: str, text: str, initial_state: dict | None = None) -> dict:
    config = {"configurable": {"thread_id": conversation_id}}
    state = initial_state if initial_state is not None else make_initial_state(conversation_id)
    graph.update_state(config, state)
    return graph.invoke(
        {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
        config,
    )


class TestOffTopicAndGreeting:
    def test_off_topic_request_is_redirected(self, graph) -> None:
        result = _run(graph, "us1-offtopic", "Recommend a movie")
        decision = result.get("guardrail_decision") or {}
        assert decision.get("outcome") == "blocked"
        assert decision.get("reason_category") == "off_topic"
        assert "healthcare" in result["reply"].lower()

    def test_greeting_is_not_blocked(self, graph) -> None:
        result = _run(graph, "us1-greeting", "Hello, how are you?")
        decision = result.get("guardrail_decision") or {}
        assert decision.get("outcome") == "allowed"


class TestVerificationAndPremium:
    def test_verification_data_allowed(self, graph) -> None:
        result = _run(graph, "us1-verify", "My name is Lisa and my phone is +14155552671")
        decision = result.get("guardrail_decision") or {}
        assert decision.get("outcome") == "allowed"
        # The guardrail did not block, so attributes were extracted and passed on.
        assert result.get("attr_phone") == "+14155552671"
        assert result.get("attr_name") is not None

    def test_premium_insurance_allowed(self, graph) -> None:
        state = make_initial_state("us1-premium")
        state["status"] = "authenticated"
        state["matched_patient_id"] = "cust-1"
        state["patient_classification"] = "premium"
        result = _run(
            graph, "us1-premium", "I need help with my insurance coverage", initial_state=state
        )
        decision = result.get("guardrail_decision") or {}
        assert decision.get("outcome") == "allowed"
        assert "insurance" in result["reply"].lower()


class TestRedirectionLoop:
    def test_repeated_off_topic_uses_brief_reply(self, graph) -> None:
        first = _run(graph, "us1-loop", "Recommend a movie")
        second = _run(graph, "us1-loop", "Recommend a movie")
        assert "how can i help you today" in first["reply"].lower()
        assert "how can i help you today" not in second["reply"].lower()


class TestClarification:
    def test_short_clarification_allowed(self, graph) -> None:
        state = make_initial_state("us1-clarify")
        state["status"] = "authenticated"
        state["matched_patient_id"] = "cust-2"
        state["patient_classification"] = "regular"
        state["support_intent"] = "ambiguous"
        result = _run(graph, "us1-clarify", "Yes, I meant my appointment", initial_state=state)
        decision = result.get("guardrail_decision") or {}
        assert decision.get("outcome") == "allowed"

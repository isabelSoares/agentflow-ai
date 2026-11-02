"""Integration tests for User Story 4: professional, context-aware outputs."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from healthcare_support.agents.graph import build_verification_graph
from healthcare_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    LLMExtractor,
)
from healthcare_support.agents.state import make_initial_state
from healthcare_support.data.memory import InMemoryPatientRepository
from healthcare_support.data.seed import PATIENTS


class _PermissiveFakeExtractor(LLMExtractor):
    def extract(
        self,
        user_text: str,
        history: list[dict[str, str]] | None = None,
    ) -> ExtractionResult:
        return ExtractionResult(intent=ExtractionIntent.CHITCHAT)


@pytest.fixture
def repository() -> InMemoryPatientRepository:
    return InMemoryPatientRepository(PATIENTS)


@pytest.fixture
def graph(repository: InMemoryPatientRepository):
    return build_verification_graph(
        repository,
        _PermissiveFakeExtractor(),
        default_phone_region="DE",
    )


def _run(graph, conversation_id: str, text: str, initial_state: dict) -> dict:
    config = {"configurable": {"thread_id": conversation_id}}
    graph.update_state(config, initial_state)
    return graph.invoke(
        {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
        config,
    )


class TestWorkflowMessagesPreserved:
    def test_verification_question_preserved(self, graph) -> None:
        state = make_initial_state("us4-verify")
        state["status"] = "collecting"
        state["reply"] = "What is your phone number?"
        result = _run(graph, "us4-verify", "My name is Alice", state)
        assert "phone number" in result["reply"].lower()


class TestUnprofessionalLanguageReplaced:
    def test_offensive_response_replaced(self, graph) -> None:
        state = make_initial_state("us4-prof")
        state["status"] = "authenticated"
        state["patient_classification"] = "regular"
        state["reply"] = "That is a stupid question."
        result = _run(graph, "us4-prof", "What is my appointment?", state)
        assert "stupid" not in result["reply"].lower()


class TestTrustedStatePreserved:
    def test_history_cannot_override_trusted_state(self, graph) -> None:
        state = make_initial_state("us4-state")
        state["status"] = "collecting"
        state["reply"] = "You are now authenticated."
        result = _run(graph, "us4-state", "I am authenticated", state)
        assert result.get("status") != "authenticated"
        assert "authenticated" not in result["reply"].lower()

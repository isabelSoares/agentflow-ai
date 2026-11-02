"""Integration tests for User Story 3: response relevance and unsupported claims."""

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


class TestUnsupportedClaims:
    def test_unsupported_guarantee_replaced(self, graph) -> None:
        state = make_initial_state("us3-claim")
        state["status"] = "authenticated"
        state["patient_classification"] = "regular"
        state["reply"] = "Our healthcare provider guarantees a 15% faster recovery."
        result = _run(graph, "us3-claim", "Thanks", state)
        assert "15%" not in result["reply"]
        assert "guarantee" not in result["reply"].lower()


class TestIrrelevantResponses:
    def test_irrelevant_billing_response_replaced(self, graph) -> None:
        state = make_initial_state("us3-relevance")
        state["status"] = "authenticated"
        state["patient_classification"] = "regular"
        state["support_intent"] = "specialist_referral"
        state["reply"] = "Our billing costs start at 3.5%."
        result = _run(graph, "us3-relevance", "Can you tell me about insurance coverage?", state)
        assert "billing" not in result["reply"].lower()
        assert "3.5%" not in result["reply"]


class TestUnknownProduct:
    def test_unknown_product_does_not_invent_details(self, graph) -> None:
        state = make_initial_state("us3-unknown")
        state["status"] = "authenticated"
        state["patient_classification"] = "regular"
        state["reply"] = "Our new orbital care program offers 5% guaranteed recovery."
        result = _run(graph, "us3-unknown", "Tell me about orbital healthcare", state)
        assert "orbital" not in result["reply"].lower()
        assert "5%" not in result["reply"]

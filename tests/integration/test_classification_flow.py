"""Integration tests for the Bouncer classification flow."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from banking_support.agents.graph import build_verification_graph
from banking_support.agents.llm import ExtractionIntent, ExtractionResult, ScriptedFakeExtractor
from banking_support.agents.state import make_initial_state
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.seed import CUSTOMERS
from banking_support.domain.conversation import ConversationStatus


@pytest.fixture
def repository() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository(CUSTOMERS)


def run_turn(graph, conversation_id: str, text: str) -> dict:
    config = {"configurable": {"thread_id": conversation_id}}
    return graph.invoke(
        {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
        config,
    )


class TestPremiumClassification:
    def test_premium_customer_routed_to_premium_support(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        )
        graph = build_verification_graph(repository, extractor)
        cid = "conv-premium-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        run_turn(graph, cid, "identify me")
        state = run_turn(graph, cid, "Yoda")
        assert state["status"] == ConversationStatus.AUTHENTICATED.value
        assert state["customer_classification"] == "premium"
        assert "+1999888999" in state["reply"]
        assert "premium client" in state["reply"].lower()


class TestRegularClassification:
    def test_regular_customer_routed_to_standard_support(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="John Doe",
                    phone="+12025550123",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Blue", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        )
        graph = build_verification_graph(repository, extractor)
        cid = "conv-regular-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        run_turn(graph, cid, "identify me")
        state = run_turn(graph, cid, "Blue")
        assert state["status"] == ConversationStatus.AUTHENTICATED.value
        assert state["customer_classification"] == "regular"
        assert "+1112112112" in state["reply"]
        assert "regular client" in state["reply"].lower()


class TestNonCustomerClassification:
    def test_unverified_caller_is_not_classified(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(intent=ExtractionIntent.REQUEST_DATA),
            ]
        )
        graph = build_verification_graph(repository, extractor)
        cid = "conv-unverified-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        state = run_turn(graph, cid, "what is my account status?")
        assert state["status"] == ConversationStatus.COLLECTING.value
        assert state["customer_classification"] is None
        assert "identity is verified" in state["reply"].lower()

    def test_verified_but_unresolvable_customer_is_non_customer(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        class MissingRecordRepository(InMemoryCustomerRepository):
            def get_by_id(self, customer_id: str) -> None:
                return None

        missing_repo = MissingRecordRepository(CUSTOMERS)
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
            ]
        )
        graph = build_verification_graph(missing_repo, extractor)
        cid = "conv-noncustomer-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        run_turn(graph, cid, "identify me")
        state = run_turn(graph, cid, "Yoda")
        assert state["status"] == ConversationStatus.AUTHENTICATED.value
        assert state["customer_classification"] == "non_customer"
        assert "existing customers" in state["reply"]


class TestClassificationStateIsolation:
    def test_new_conversation_has_no_classification(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        extractor = ScriptedFakeExtractor([])
        graph = build_verification_graph(repository, extractor)
        cid = "conv-fresh-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        state = run_turn(graph, cid, "hello")
        assert state["customer_classification"] is None

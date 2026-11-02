"""Integration tests for conversation history features (US1-US6)."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from healthcare_support.agents.graph import build_verification_graph
from healthcare_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from healthcare_support.agents.state import make_initial_state
from healthcare_support.data.memory import InMemoryCustomerRepository
from healthcare_support.data.seed import CUSTOMERS
from healthcare_support.domain.conversation import ConversationStatus
from healthcare_support.domain.routing import IntentClassification, SupportIntent


@pytest.fixture
def repository() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository(CUSTOMERS)


def run_turn(graph, conversation_id: str, text: str) -> dict:
    config = {"configurable": {"thread_id": conversation_id}}
    return graph.invoke(
        {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
        config,
    )


class TestUS1MultiTurnContext:
    def test_follow_up_references_prior_context(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        # Authenticate first, then test that the Specialist uses history to
        # interpret a short contextual follow-up.
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
                ExtractionResult(
                    intent=ExtractionIntent.CHITCHAT,
                ),
                ExtractionResult(
                    intent=ExtractionIntent.CHITCHAT,
                ),
            ]
        )
        classifier = ScriptedFakeSupportIntentClassifier(
            [
                IntentClassification(
                    intent=SupportIntent.YACHT_INSURANCE,
                    needs_clarification=True,
                    clarification_prompt="Is this for a private or commercial yacht?",
                ),
                IntentClassification(
                    intent=SupportIntent.YACHT_INSURANCE,
                    needs_clarification=False,
                ),
            ]
        )
        graph = build_verification_graph(
            repository,
            extractor,
            intent_classifier=classifier,
        )
        cid = "conv-us1-context"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))

        run_turn(graph, cid, "I am Lisa, phone +14155552671")
        auth_state = run_turn(graph, cid, "Yoda")
        assert auth_state["status"] == ConversationStatus.AUTHENTICATED.value

        state1 = run_turn(graph, cid, "I need yacht insurance")
        assert "private or commercial" in state1["reply"].lower()

        state2 = run_turn(graph, cid, "For a private yacht")
        assert state2["support_intent"] == SupportIntent.YACHT_INSURANCE.value


class TestUS2VerificationAcrossMessages:
    def test_name_then_phone_advances(self, repository: InMemoryCustomerRepository) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(name="Lisa", intent=ExtractionIntent.PROVIDE_IDENTIFICATION),
                ExtractionResult(
                    phone="+14155552671", intent=ExtractionIntent.PROVIDE_IDENTIFICATION
                ),
            ]
        )
        graph = build_verification_graph(repository, extractor)
        cid = "conv-us2-verify"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))

        state1 = run_turn(graph, cid, "My name is Lisa")
        assert state1["status"] == ConversationStatus.COLLECTING.value
        assert "more information" in state1["reply"].lower()

        state2 = run_turn(graph, cid, "My phone is +14155552671")
        assert state2["status"] == ConversationStatus.IDENTIFIED.value
        assert "Which is the name of my dog?" in state2["reply"]


class TestUS3SessionIsolation:
    def test_sessions_do_not_share_history(self, repository: InMemoryCustomerRepository) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(name="Lisa", intent=ExtractionIntent.PROVIDE_IDENTIFICATION),
                ExtractionResult(name="Maria", intent=ExtractionIntent.PROVIDE_IDENTIFICATION),
            ]
        )
        graph = build_verification_graph(repository, extractor)

        cid_a = "conv-us3-a"
        cid_b = "conv-us3-b"
        graph.update_state({"configurable": {"thread_id": cid_a}}, make_initial_state(cid_a))
        graph.update_state({"configurable": {"thread_id": cid_b}}, make_initial_state(cid_b))

        state_a = run_turn(graph, cid_a, "I am Lisa")
        state_b = run_turn(graph, cid_b, "I am Maria")

        assert state_a["attr_name"] == "Lisa"
        assert state_b["attr_name"] == "Maria"
        assert "Lisa" not in state_b["reply"]
        assert "Maria" not in state_a["reply"]


class TestUS4SessionReset:
    def test_reset_clears_state(self, repository: InMemoryCustomerRepository) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
            ]
        )
        graph = build_verification_graph(repository, extractor)
        cid = "conv-us4-reset"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))

        state = run_turn(graph, cid, "I am Lisa, phone +14155552671")
        assert state["status"] == ConversationStatus.IDENTIFIED.value

        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))

        state2 = run_turn(graph, cid, "hello")
        assert state2["status"] == ConversationStatus.COLLECTING.value
        assert state2["attr_name"] is None


class TestUS5ContextAwareGuardrails:
    def test_short_contextual_reply_allowed(self, repository: InMemoryCustomerRepository) -> None:
        extractor = ScriptedFakeExtractor(
            [
                ExtractionResult(
                    name="Lisa",
                    phone="+14155552671",
                    intent=ExtractionIntent.PROVIDE_IDENTIFICATION,
                ),
                ExtractionResult(secret_answer="Yoda", intent=ExtractionIntent.ANSWER_SECRET),
                ExtractionResult(intent=ExtractionIntent.CHITCHAT),
            ]
        )
        classifier = ScriptedFakeSupportIntentClassifier(
            [
                IntentClassification(
                    intent=SupportIntent.INSURANCE,
                    needs_clarification=True,
                    clarification_prompt="What type of insurance?",
                ),
                IntentClassification(
                    intent=SupportIntent.INSURANCE,
                    needs_clarification=False,
                ),
            ]
        )
        graph = build_verification_graph(
            repository,
            extractor,
            intent_classifier=classifier,
        )
        cid = "conv-us5-guardrails"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))

        run_turn(graph, cid, "I am Lisa, phone +14155552671")
        run_turn(graph, cid, "Yoda")

        state = run_turn(graph, cid, "I need insurance")
        assert "type of insurance" in state["reply"].lower()

        state2 = run_turn(graph, cid, "For my yacht")
        assert state2["support_intent"] == SupportIntent.INSURANCE.value


class TestUS6HistoryLimitsAndFailure:
    def test_long_conversation_preserves_trusted_state(
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
            + [ExtractionResult(intent=ExtractionIntent.CHITCHAT)] * 25
        )
        graph = build_verification_graph(repository, extractor)
        cid = "conv-us6-limits"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))

        run_turn(graph, cid, "I am Lisa, phone +14155552671")
        auth_state = run_turn(graph, cid, "Yoda")
        assert auth_state["status"] == ConversationStatus.AUTHENTICATED.value
        assert auth_state["customer_classification"] == "premium"

        # Send many chitchat turns; authentication/classification state must survive.
        final_state = auth_state
        for i in range(25):
            final_state = run_turn(graph, cid, f"turn {i}")

        assert final_state["status"] == ConversationStatus.AUTHENTICATED.value
        assert final_state["customer_classification"] == "premium"

"""Integration tests for the Bouncer classification flow."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from healthcare_support.agents.graph import build_verification_graph
from healthcare_support.agents.llm import ExtractionIntent, ExtractionResult, ScriptedFakeExtractor
from healthcare_support.agents.state import make_initial_state
from healthcare_support.data.memory import InMemoryPatientRepository
from healthcare_support.data.seed import PATIENTS
from healthcare_support.domain.conversation import ConversationStatus


@pytest.fixture
def repository() -> InMemoryPatientRepository:
    return InMemoryPatientRepository(PATIENTS)


def run_turn(graph, conversation_id: str, text: str) -> dict:
    config = {"configurable": {"thread_id": conversation_id}}
    return graph.invoke(
        {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
        config,
    )


class TestPremiumClassification:
    def test_premium_patient_routed_to_premium_support(
        self, repository: InMemoryPatientRepository
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
        assert state["patient_classification"] == "premium"
        assert "+1999888999" in state["reply"]
        assert "premium client" in state["reply"].lower()


class TestRegularClassification:
    def test_regular_patient_routed_to_standard_support(
        self, repository: InMemoryPatientRepository
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
        assert state["patient_classification"] == "regular"
        assert "+1112112112" in state["reply"]
        assert "regular client" in state["reply"].lower()


class TestNonPatientClassification:
    def test_unverified_caller_is_not_classified(
        self, repository: InMemoryPatientRepository
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
        assert state["patient_classification"] is None
        assert "identity is verified" in state["reply"].lower()

    def test_verified_but_unresolvable_patient_is_non_patient(
        self, repository: InMemoryPatientRepository
    ) -> None:
        class MissingRecordRepository(InMemoryPatientRepository):
            def get_by_id(self, patient_id: str) -> None:
                return None

        missing_repo = MissingRecordRepository(PATIENTS)
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
        cid = "conv-nonpatient-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        run_turn(graph, cid, "identify me")
        state = run_turn(graph, cid, "Yoda")
        assert state["status"] == ConversationStatus.AUTHENTICATED.value
        assert state["patient_classification"] == "non_patient"
        assert "existing patients" in state["reply"]


class TestClassificationStateIsolation:
    def test_new_conversation_has_no_classification(
        self, repository: InMemoryPatientRepository
    ) -> None:
        extractor = ScriptedFakeExtractor([])
        graph = build_verification_graph(repository, extractor)
        cid = "conv-fresh-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        state = run_turn(graph, cid, "hello")
        assert state["patient_classification"] is None

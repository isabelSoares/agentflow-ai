"""Integration tests for the Specialist routing flow."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from banking_support.agents.graph import build_verification_graph
from banking_support.agents.llm import (
    ExtractionIntent,
    ExtractionResult,
    ScriptedFakeExtractor,
    ScriptedFakeSupportIntentClassifier,
)
from banking_support.agents.state import make_initial_state
from banking_support.data.memory import InMemoryCustomerRepository
from banking_support.data.seed import CUSTOMERS
from banking_support.domain.conversation import ConversationStatus
from banking_support.domain.routing import (
    IntentClassification,
    SupportDepartment,
    SupportIntent,
)


@pytest.fixture
def repository() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository(CUSTOMERS)


def _run_turn(graph, conversation_id: str, text: str) -> dict:
    config = {"configurable": {"thread_id": conversation_id}}
    return graph.invoke(
        {"messages": [HumanMessage(content=text)], "conversation_id": conversation_id},
        config,
    )


def _authenticate_lisa(graph, cid: str, repository: InMemoryCustomerRepository) -> dict:
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
    graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
    _run_turn(graph, cid, "identify me")
    return _run_turn(graph, cid, "Yoda")


class TestPremiumSpecialistRouting:
    def test_premium_yacht_insurance_routes_to_specialist(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.YACHT_INSURANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-premium-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        auth_state = _run_turn(graph, cid, "identify me")
        assert auth_state["status"] == ConversationStatus.IDENTIFIED.value

        auth_state = _run_turn(graph, cid, "Yoda")
        assert auth_state["status"] == ConversationStatus.AUTHENTICATED.value
        assert auth_state["customer_classification"] == "premium"

        state = _run_turn(graph, cid, "I need yacht insurance")
        assert state["status"] == ConversationStatus.AUTHENTICATED.value
        assert state["routing_status"] == "routed"
        assert state["support_intent"] == "yacht_insurance"
        assert state["support_department"] == "Insurance Specialist Department"
        assert state["routing_contact"] == "+18005551234"
        assert "Insurance Specialist Department" in state["reply"]

    def test_premium_account_assistance_routes_to_premium_support(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.ACCOUNT_ASSISTANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-premium-2"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        state = _run_turn(graph, cid, "I need account help")
        assert state["routing_status"] == "routed"
        assert state["support_intent"] == "account_assistance"
        assert state["support_department"] == "Premium Customer Support"
        assert state["routing_contact"] == "+1999888999"

    def test_unavailable_specialist_returns_fallback(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        from banking_support.data.support_directory import default_support_directory
        from banking_support.domain.routing import SupportDirectory

        base = default_support_directory()
        directory = SupportDirectory(
            departments={
                k: (
                    SupportDepartment(
                        key=v.key,
                        display_name=v.display_name,
                        contact=v.contact,
                        specializations=v.specializations,
                        available=False,
                    )
                    if k == "insurance_specialist"
                    else v
                )
                for k, v in base.departments.items()
            }
        )
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.YACHT_INSURANCE)]
        )
        graph = build_verification_graph(
            repository, extractor, intent_classifier=classifier, support_directory=directory
        )
        cid = "conv-specialist-premium-3"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        state = _run_turn(graph, cid, "I need yacht insurance")
        assert state["routing_status"] == "fallback"
        assert state["support_department"] is None


class TestRegularRouting:
    def test_regular_account_assistance_routes_to_standard_support(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.ACCOUNT_ASSISTANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-regular-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Blue")
        state = _run_turn(graph, cid, "I need account help")
        assert state["status"] == ConversationStatus.AUTHENTICATED.value
        assert state["customer_classification"] == "regular"
        assert state["routing_status"] == "routed"
        assert state["support_intent"] == "account_assistance"
        assert state["support_department"] == "Standard Customer Support"
        assert state["routing_contact"] == "+1112112112"

    def test_regular_yacht_insurance_routes_to_specialist(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.YACHT_INSURANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-regular-2"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Blue")
        state = _run_turn(graph, cid, "I need yacht insurance")
        assert state["routing_status"] == "routed"
        assert state["support_intent"] == "yacht_insurance"
        assert state["support_department"] == "Insurance Specialist Department"


class TestClarificationAndFallback:
    def test_ambiguous_request_asks_clarification(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [
                IntentClassification(
                    intent=SupportIntent.AMBIGUOUS,
                    needs_clarification=True,
                    clarification_prompt="Do you need account help or insurance?",
                )
            ]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-clarify-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        state = _run_turn(graph, cid, "I need help")
        assert state["routing_status"] == "clarification_required"
        assert state["support_intent"] == "ambiguous"
        assert state["support_department"] is None
        assert "Do you need account help or insurance?" in state["reply"]

    def test_unsupported_request_returns_fallback(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.UNSUPPORTED)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-fallback-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        state = _run_turn(graph, cid, "I want to buy a car")
        assert state["routing_status"] == "fallback"
        assert state["support_department"] is None
        assert state["routing_contact"] is None

    def test_failed_classifier_returns_fallback(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.UNINTERPRETABLE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-fail-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        state = _run_turn(graph, cid, "...")
        assert state["routing_status"] == "fallback"


class TestAuthenticationBoundary:
    def test_unauthenticated_request_is_not_routed(
        self, repository: InMemoryCustomerRepository
    ) -> None:
        extractor = ScriptedFakeExtractor([ExtractionResult(intent=ExtractionIntent.CHITCHAT)])
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.ACCOUNT_ASSISTANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-unauth-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        state = _run_turn(graph, cid, "I need help with my account")
        assert state["status"] == ConversationStatus.COLLECTING.value
        assert state["status"] != ConversationStatus.AUTHENTICATED.value
        assert state["routing_status"] is None
        assert state["support_department"] is None

    def test_missing_classification_is_blocked(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.ACCOUNT_ASSISTANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-noclass-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        # Tamper with the state to remove classification before the next turn.
        config = {"configurable": {"thread_id": cid}}
        graph.update_state(config, {"customer_classification": None})
        state = _run_turn(graph, cid, "I need account help")
        assert state["routing_status"] == "blocked"
        assert state["support_department"] is None


class TestNoPiiExposure:
    def test_routing_response_does_not_expose_customer_records(
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
        classifier = ScriptedFakeSupportIntentClassifier(
            [IntentClassification(intent=SupportIntent.ACCOUNT_ASSISTANCE)]
        )
        graph = build_verification_graph(repository, extractor, intent_classifier=classifier)
        cid = "conv-specialist-pii-1"
        graph.update_state({"configurable": {"thread_id": cid}}, make_initial_state(cid))
        _run_turn(graph, cid, "identify me")
        _run_turn(graph, cid, "Yoda")
        state = _run_turn(graph, cid, "I need account help")
        reply = state["reply"]
        for customer in CUSTOMERS:
            assert customer.phone not in reply
            assert customer.iban not in reply
            assert customer.secret_answer not in reply
            assert customer.name not in reply

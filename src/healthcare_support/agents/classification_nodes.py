"""Factory for the authenticated customer classification node."""

from __future__ import annotations

from typing import Any

from healthcare_support.agents.node_strategies import WorkflowDependencies
from healthcare_support.agents.state import GraphState
from healthcare_support.core import classification
from healthcare_support.core.responses import (
    NON_CUSTOMER_RESPONSE,
    PREMIUM_ROUTING,
    REGULAR_ROUTING,
)
from healthcare_support.domain.conversation import ConversationStatus, CustomerClassification
from healthcare_support.observability.audit import build_audit_event, emit


def make_classification_node(dependencies: WorkflowDependencies) -> Any:
    def classify_node(state: GraphState) -> dict[str, Any]:
        if state["status"] != ConversationStatus.AUTHENTICATED.value:
            return {}
        matched_id = state.get("matched_customer_id")
        if matched_id is None:
            return _classification_error(state)
        try:
            customer = dependencies.repository.get_by_id(matched_id)
            customer_classification = classification.classify_customer(customer, is_verified=True)
        except Exception:
            return _classification_error(state)

        reply = {
            CustomerClassification.PREMIUM: PREMIUM_ROUTING,
            CustomerClassification.REGULAR: REGULAR_ROUTING,
        }.get(customer_classification, NON_CUSTOMER_RESPONSE)
        emit(
            build_audit_event(
                event_type="classified",
                conversation_id=state.get("conversation_id", ""),
                identified=True,
                authenticated=True,
                identification_attempts=state["identification_attempts"],
                secret_answer_attempts=state["secret_answer_attempts"],
                classification=customer_classification.value,
            )
        )
        return {"customer_classification": customer_classification.value, "reply": reply}

    return classify_node


def _classification_error(state: GraphState) -> dict[str, Any]:
    emit(
        build_audit_event(
            event_type="classification_error",
            conversation_id=state.get("conversation_id", ""),
            identified=True,
            authenticated=True,
            identification_attempts=state["identification_attempts"],
            secret_answer_attempts=state["secret_answer_attempts"],
        )
    )
    return {
        "customer_classification": CustomerClassification.NON_CUSTOMER.value,
        "reply": NON_CUSTOMER_RESPONSE,
    }


__all__ = ["make_classification_node"]

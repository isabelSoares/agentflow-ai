"""Factory for authenticated specialist routing."""

from __future__ import annotations

from typing import Any

from healthcare_support.agents.node_strategies import (
    WorkflowDependencies,
    last_user_text,
    sanitized_history,
)
from healthcare_support.agents.state import GraphState
from healthcare_support.core.routing import route_support_request
from healthcare_support.domain.conversation import ConversationStatus, CustomerClassification
from healthcare_support.observability.audit import build_audit_event, emit


def make_specialist_node(dependencies: WorkflowDependencies) -> Any:
    def specialist_node(state: GraphState) -> dict[str, Any]:
        if state.get("status") != ConversationStatus.AUTHENTICATED.value:
            return {}
        if dependencies.intent_classifier is None:
            return {}
        classification_value = state.get("customer_classification")
        try:
            customer_classification = (
                CustomerClassification(classification_value)
                if classification_value is not None
                else None
            )
        except ValueError:
            customer_classification = None

        intent_classification = dependencies.intent_classifier.classify(
            last_user_text(state), sanitized_history(state)
        )
        decision = route_support_request(
            is_authenticated=True,
            customer_classification=customer_classification,
            intent_classification=intent_classification,
            support_directory=dependencies.support_directory,
        )
        emit(
            build_audit_event(
                event_type="routed",
                conversation_id=state.get("conversation_id", ""),
                identified=True,
                authenticated=True,
                identification_attempts=state["identification_attempts"],
                secret_answer_attempts=state["secret_answer_attempts"],
                classification=classification_value,
                routing_status=decision.status.value,
                routing_intent=decision.intent.value,
                department_key=decision.department_key,
            )
        )
        return {
            "reply": decision.message,
            "support_intent": decision.intent.value,
            "support_specialization": intent_classification.specialization,
            "routing_status": decision.status.value,
            "support_department": decision.department_name,
            "routing_contact": decision.contact,
        }

    return specialist_node


__all__ = ["make_specialist_node"]

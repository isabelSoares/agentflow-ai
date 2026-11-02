"""Factory for the authenticated patient classification node."""

from __future__ import annotations

from typing import Any

from healthcare_support.agents.node_strategies import WorkflowDependencies
from healthcare_support.agents.state import GraphState
from healthcare_support.core import classification
from healthcare_support.core.responses import (
    NON_PATIENT_RESPONSE,
    PREMIUM_ROUTING,
    REGULAR_ROUTING,
)
from healthcare_support.domain.conversation import ConversationStatus, PatientClassification
from healthcare_support.observability.audit import build_audit_event, emit


def make_classification_node(dependencies: WorkflowDependencies) -> Any:
    def classify_node(state: GraphState) -> dict[str, Any]:
        if state["status"] != ConversationStatus.AUTHENTICATED.value:
            return {}
        matched_id = state.get("matched_patient_id")
        if matched_id is None:
            return _classification_error(state)
        try:
            patient = dependencies.repository.get_by_id(matched_id)
            patient_classification = classification.classify_patient(patient, is_verified=True)
        except Exception:
            return _classification_error(state)

        reply = {
            PatientClassification.PREMIUM: PREMIUM_ROUTING,
            PatientClassification.REGULAR: REGULAR_ROUTING,
        }.get(patient_classification, NON_PATIENT_RESPONSE)
        emit(
            build_audit_event(
                event_type="classified",
                conversation_id=state.get("conversation_id", ""),
                identified=True,
                authenticated=True,
                identification_attempts=state["identification_attempts"],
                secret_answer_attempts=state["secret_answer_attempts"],
                classification=patient_classification.value,
            )
        )
        return {"patient_classification": patient_classification.value, "reply": reply}

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
        "patient_classification": PatientClassification.NON_PATIENT.value,
        "reply": NON_PATIENT_RESPONSE,
    }


__all__ = ["make_classification_node"]

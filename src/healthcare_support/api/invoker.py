"""Graph invocation helpers for API routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request

from healthcare_support.agents.state import GraphState, make_initial_state
from healthcare_support.api.app import AppState
from healthcare_support.data.session_access import AccessDecision, SessionAccessStore
from healthcare_support.observability.audit import build_audit_event, emit

logger = logging.getLogger(__name__)

SESSION_ACCESS_DENIED_DETAIL = "Session access denied."


def get_app_state(request: Request) -> AppState:
    return request.app.state.app_state  # type: ignore[no-any-return]


def _store(app_state: AppState) -> SessionAccessStore:
    return app_state.session_access_store


def _deny_access(conversation_id: str, decision: AccessDecision) -> None:
    """Emit a redacted audit event and raise the uniform denial response."""
    emit(
        build_audit_event(
            event_type="session_access_denied",
            conversation_id=conversation_id,
            access_outcome=decision.value,
            access_reason=decision.value,
        )
    )
    raise HTTPException(status_code=401, detail=SESSION_ACCESS_DENIED_DETAIL)


def ensure_session_access(app_state: AppState, conversation_id: str, proof: str | None) -> None:
    """Verify session ownership or raise the uniform denial response."""
    decision = _store(app_state).verify(conversation_id, proof)
    if decision is not AccessDecision.GRANTED:
        _deny_access(conversation_id, decision)
    emit(
        build_audit_event(
            event_type="session_access_granted",
            conversation_id=conversation_id,
            access_outcome=decision.value,
        )
    )


def _sensitive_values_for_state(state: GraphState, app_state: AppState) -> set[str]:
    """Collect sensitive values that must be redacted from persisted history."""
    sensitive: set[str] = set()
    matched_id = state.get("matched_patient_id")
    if matched_id is not None:
        patient = app_state.patient_repository.get_by_id(matched_id)
        if patient is not None:
            sensitive.update(
                value
                for value in (
                    patient.name,
                    patient.phone,
                    patient.date_of_birth,
                    patient.secret_answer,
                )
                if value
            )
    return sensitive


def invoke_graph(
    app_state: AppState,
    conversation_id: str,
    text: str,
    presented_proof: str | None = None,
) -> GraphState:
    """Invoke the verification graph for a single user turn.

    Session access is verified before any graph or history state is touched. The
    raw user input is passed through ``user_input`` so that the graph nodes can
    process it, while persisted history is redacted before storage.
    """
    ensure_session_access(app_state, conversation_id, presented_proof)

    graph = app_state.verification_graph
    history_store = app_state.history_store
    config = {"configurable": {"thread_id": conversation_id}}

    snapshot = graph.get_state(config)
    if not snapshot.values or snapshot.values.get("status") is None:
        # A verified session with no usable checkpoint is re-initialized without
        # inheriting prior state. The identifier is never adopted on its own.
        graph.update_state(config, make_initial_state(conversation_id))

    input_state: dict[str, Any] = {
        "user_input": text,
        "conversation_id": conversation_id,
    }

    result: GraphState = graph.invoke(input_state, config)

    if result.get("terminated"):
        _store(app_state).deactivate(conversation_id)
        emit(
            build_audit_event(
                event_type="session_terminated",
                conversation_id=conversation_id,
                terminated=True,
                termination_reason=result.get("termination_reason"),
            )
        )

    # Persist the redacted user message and the assistant reply so that the
    # conversation history remains useful for context while protecting secrets.
    try:
        sensitive_values = _sensitive_values_for_state(result, app_state)
        history_store.add_user_message(conversation_id, text, sensitive_values=sensitive_values)
        reply = result.get("reply")
        if reply:
            history_store.add_assistant_message(conversation_id, str(reply))
    except Exception:
        # History unavailability must not leak data, bypass security checks, or
        # expose internal errors to the patient.
        logger.exception("Failed to persist conversation history")

    return result


def reset_conversation(
    app_state: AppState,
    conversation_id: str,
    presented_proof: str | None = None,
) -> tuple[GraphState, str]:
    """Reset an authorized conversation and rotate its ownership proof."""
    ensure_session_access(app_state, conversation_id, presented_proof)

    app_state.history_store.reset_session(conversation_id)
    new_proof = _store(app_state).rotate(conversation_id)
    emit(
        build_audit_event(
            event_type="session_reset",
            conversation_id=conversation_id,
            access_outcome=AccessDecision.GRANTED.value,
        )
    )
    config = {"configurable": {"thread_id": conversation_id}}
    snapshot = app_state.verification_graph.get_state(config)
    return snapshot.values, new_proof


__all__ = [
    "SESSION_ACCESS_DENIED_DETAIL",
    "ensure_session_access",
    "get_app_state",
    "invoke_graph",
    "reset_conversation",
]

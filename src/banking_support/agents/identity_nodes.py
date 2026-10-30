"""Factories for identification and authentication graph nodes."""

from __future__ import annotations

from typing import Any

from banking_support.agents.node_strategies import WorkflowDependencies, find_customer
from banking_support.agents.state import GraphState
from banking_support.core import matching, verification
from banking_support.core.responses import (
    ASK_DISAMBIGUATION,
    ASK_MORE_ATTRIBUTES,
    DATA_REQUEST_REFUSAL,
    IDENTIFICATION_FAILURE,
    SECRET_QUESTION_PREFIX,
)
from banking_support.domain.conversation import (
    ConversationStatus,
    ExtractionIntent,
    ProvidedAttributes,
)
from banking_support.observability.audit import build_audit_event, emit

MAX_ATTEMPTS = verification.MAX_ATTEMPTS


def make_identity_nodes(dependencies: WorkflowDependencies) -> dict[str, Any]:
    def identify_node(state: GraphState) -> dict[str, Any]:
        if state["status"] != ConversationStatus.COLLECTING.value:
            return {}
        if state.get("extraction_intent") == ExtractionIntent.REQUEST_DATA.value:
            return {"reply": DATA_REQUEST_REFUSAL}

        attrs = ProvidedAttributes(
            name=state.get("attr_name"), phone=state.get("attr_phone"), iban=state.get("attr_iban")
        )
        result = matching.evaluate_match(
            attrs, dependencies.repository, dependencies.default_phone_region
        )
        if result.outcome == matching.MatchOutcome.UNIQUE:
            customer = result.customers[0]
            emit(
                build_audit_event(
                    event_type="identified",
                    conversation_id=state.get("conversation_id", ""),
                    identified=True,
                    identification_attempts=state["identification_attempts"],
                )
            )
            return {
                "status": ConversationStatus.IDENTIFIED.value,
                "matched_customer_id": customer.id,
                "reply": f"{SECRET_QUESTION_PREFIX}{customer.secret_question}",
            }
        if result.outcome == matching.MatchOutcome.AMBIGUOUS:
            emit(
                build_audit_event(
                    event_type="ambiguous_match",
                    conversation_id=state.get("conversation_id", ""),
                    identification_attempts=state["identification_attempts"],
                )
            )
            return {"reply": ASK_DISAMBIGUATION}
        if result.outcome == matching.MatchOutcome.INSUFFICIENT_DATA:
            return {"reply": ASK_MORE_ATTRIBUTES}

        new_attempts = state["identification_attempts"] + 1
        emit(
            build_audit_event(
                event_type="identification_attempt",
                conversation_id=state.get("conversation_id", ""),
                identification_attempts=new_attempts,
            )
        )
        if new_attempts >= MAX_ATTEMPTS:
            failure = verification.process_identification_failure(state["identification_attempts"])
            return {
                "identification_attempts": new_attempts,
                "terminated": True,
                "termination_reason": failure.termination_reason,
                "reply": failure.reply,
            }
        return {"identification_attempts": new_attempts, "reply": IDENTIFICATION_FAILURE}

    def authenticate_node(state: GraphState) -> dict[str, Any]:
        if state["status"] != ConversationStatus.IDENTIFIED.value:
            return {}
        customer = find_customer(dependencies.repository, state.get("matched_customer_id"))
        if customer is None:
            return {"reply": IDENTIFICATION_FAILURE}
        intent = state.get("extraction_intent")
        provided = state.get("pending_secret_answer")
        if provided is None or not str(provided).strip():
            if intent == ExtractionIntent.REQUEST_DATA.value:
                return {"reply": DATA_REQUEST_REFUSAL}
            return {"reply": f"{SECRET_QUESTION_PREFIX}{customer.secret_question}"}

        result = verification.process_secret_attempt(
            provided, customer, state["secret_answer_attempts"]
        )
        if result.authenticated:
            emit(
                build_audit_event(
                    event_type="auth_success",
                    conversation_id=state.get("conversation_id", ""),
                    identified=True,
                    authenticated=True,
                    identification_attempts=state["identification_attempts"],
                    secret_answer_attempts=state["secret_answer_attempts"],
                )
            )
            return {"status": ConversationStatus.AUTHENTICATED.value, "reply": result.reply}

        new_attempts = state["secret_answer_attempts"] + 1
        emit(
            build_audit_event(
                event_type="auth_failure",
                conversation_id=state.get("conversation_id", ""),
                identified=True,
                identification_attempts=state["identification_attempts"],
                secret_answer_attempts=new_attempts,
            )
        )
        if result.terminated:
            return {
                "secret_answer_attempts": new_attempts,
                "terminated": True,
                "termination_reason": result.termination_reason,
                "reply": result.reply,
            }
        return {"secret_answer_attempts": new_attempts, "reply": result.reply}

    return {"identify": identify_node, "authenticate": authenticate_node}


__all__ = ["make_identity_nodes"]

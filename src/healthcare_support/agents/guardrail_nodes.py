"""Factories for input and output guardrail graph nodes."""

from __future__ import annotations

from typing import Any

from healthcare_support.agents.node_strategies import (
    WorkflowDependencies,
    build_guardrail_input,
    emit_guardrail_event,
    find_patient,
    last_user_text,
    safe_reply_for,
)
from healthcare_support.agents.state import GraphState
from healthcare_support.core.responses import EMPTY_RE_PROMPT
from healthcare_support.services.guardrails_service import build_guardrail_evaluator


def make_guardrail_nodes(dependencies: WorkflowDependencies) -> dict[str, Any]:
    evaluator = build_guardrail_evaluator()

    def guardrail_node(state: GraphState) -> dict[str, Any]:
        text = last_user_text(state)
        if not text.strip():
            return {"reply": EMPTY_RE_PROMPT}
        decision = evaluator.evaluate(
            build_guardrail_input(state, content_type="patient_input", content=text)
        )
        emit_guardrail_event(state, decision)
        if decision.outcome.value != "allowed":
            return {
                "guardrail_decision": decision.model_dump(),
                "reply": safe_reply_for(decision),
            }
        return {"guardrail_decision": decision.model_dump(), "reply": None}

    def output_guardrail_node(state: GraphState) -> dict[str, Any]:
        reply = state.get("reply")
        if reply is None:
            return {}
        prior = state.get("guardrail_decision")
        if isinstance(prior, dict) and prior.get("outcome") not in (None, "allowed"):
            return {}

        sensitive_values: set[str] = set()
        patient = find_patient(dependencies.repository, state.get("matched_patient_id"))
        if patient is not None:
            sensitive_values.update(
                value
                for value in (
                    patient.name,
                    patient.phone,
                    patient.date_of_birth,
                    patient.secret_answer,
                )
                if value
            )
        decision = evaluator.evaluate(
            build_guardrail_input(
                state,
                content_type="assistant_output",
                content=reply,
                sensitive_values=frozenset(sensitive_values),
            )
        )
        emit_guardrail_event(state, decision)
        if decision.outcome.value != "allowed":
            return {
                "guardrail_decision": decision.model_dump(),
                "reply": safe_reply_for(decision),
            }
        return {"guardrail_decision": decision.model_dump()}

    return {"guardrail": guardrail_node, "output_guardrail": output_guardrail_node}


__all__ = ["make_guardrail_nodes"]

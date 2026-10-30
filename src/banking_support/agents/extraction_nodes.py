"""Factory for the extraction graph node."""

from __future__ import annotations

from typing import Any

from banking_support.agents.node_strategies import (
    WorkflowDependencies,
    last_user_text,
    sanitized_history,
)
from banking_support.agents.state import GraphState


def make_extraction_node(dependencies: WorkflowDependencies) -> Any:
    def extract_node(state: GraphState) -> dict[str, Any]:
        result = dependencies.extractor.extract(last_user_text(state), sanitized_history(state))
        updates: dict[str, Any] = {
            "extraction_intent": result.intent.value,
            "pending_secret_answer": result.secret_answer,
        }
        if result.name is not None:
            updates["attr_name"] = result.name
        if result.phone is not None:
            updates["attr_phone"] = result.phone
        if result.iban is not None:
            updates["attr_iban"] = result.iban
        return updates

    return extract_node


__all__ = ["make_extraction_node"]

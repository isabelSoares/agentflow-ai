"""Factories for response and termination graph nodes."""

from __future__ import annotations

from typing import Any

from banking_support.agents.state import GraphState
from banking_support.core.responses import CLOSED_CONVERSATION, GREETING


def make_response_nodes() -> dict[str, Any]:
    def respond_node(state: GraphState) -> dict[str, Any]:
        reply = state.get("reply")
        return {"reply": reply if reply is not None else GREETING}

    def terminated_node(state: GraphState) -> dict[str, Any]:
        return {"reply": CLOSED_CONVERSATION}

    return {"respond": respond_node, "terminated": terminated_node}


__all__ = ["make_response_nodes"]

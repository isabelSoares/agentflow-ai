"""In-memory conversation history store backed by the LangGraph checkpointer.

The store is a thin wrapper around the existing graph state. It does not
introduce a second persistence layer; instead it provides history-specific
operations (sanitization, truncation, redaction, reset) over the checkpointed
``messages`` channel.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from healthcare_support.agents.state import make_initial_state
from healthcare_support.core.history import redact_message, sanitize_history


class GraphInvoker(Protocol):
    """Minimal protocol for the operations the store needs from the graph."""

    def get_state(self, config: dict[str, Any]) -> Any: ...
    def update_state(self, config: dict[str, Any], values: dict[str, Any]) -> Any: ...


class HistoryStore:
    """Manage conversation history for a single session.

    The store treats the session identifier as an untrusted input. It never
    derives authentication or classification from the identifier; those remain
    in the graph's trusted workflow state.
    """

    def __init__(
        self,
        graph: GraphInvoker,
        max_history_messages: int = 20,
        redaction_enabled: bool = True,
    ) -> None:
        self._graph = graph
        self._max_history_messages = max_history_messages
        self._redaction_enabled = redaction_enabled

    def _config(self, conversation_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": conversation_id}}

    def get_history(
        self,
        conversation_id: str,
        max_messages: int | None = None,
    ) -> list[dict[str, str]]:
        """Return the sanitized, truncated recent history for a session."""
        snapshot = self._graph.get_state(self._config(conversation_id))
        values = snapshot.values if snapshot else None
        messages: Sequence[BaseMessage] = values.get("messages", []) if values else []
        limit = max_messages if max_messages is not None else self._max_history_messages
        return sanitize_history(messages, limit)

    def _redact(self, text: str, sensitive_values: set[str] | None = None) -> str:
        if not self._redaction_enabled:
            return text
        return redact_message(text, sensitive_values or set(), enable_patterns=True)

    def add_user_message(
        self,
        conversation_id: str,
        content: str,
        sensitive_values: set[str] | None = None,
    ) -> None:
        """Append a redacted user message to the session history."""
        redacted = self._redact(content, sensitive_values)
        self._graph.update_state(
            self._config(conversation_id),
            {"messages": [HumanMessage(content=redacted)]},
        )

    def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
    ) -> None:
        """Append an assistant message to the session history."""
        self._graph.update_state(
            self._config(conversation_id),
            {"messages": [AIMessage(content=content)]},
        )

    def reset_session(self, conversation_id: str) -> None:
        """Clear history and invalidate trusted workflow state for a session."""
        cleared_state = make_initial_state(conversation_id)
        # An empty message list is a no-op for LangGraph's add_messages reducer,
        # so removal must be explicit.
        cleared_state["messages"] = [RemoveMessage(id=REMOVE_ALL_MESSAGES)]
        self._graph.update_state(
            self._config(conversation_id),
            cleared_state,
        )

    def session_exists(self, conversation_id: str) -> bool:
        """Return True if the graph has checkpointed state for the session."""
        snapshot = self._graph.get_state(self._config(conversation_id))
        return bool(snapshot and snapshot.values)


__all__ = ["HistoryStore", "GraphInvoker"]

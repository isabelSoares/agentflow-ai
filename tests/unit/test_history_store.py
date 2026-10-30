"""Unit tests for the conversation history store."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from banking_support.data.history_store import HistoryStore


class FakeGraph:
    """In-memory fake of the minimal graph operations the store uses."""

    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}

    def get_state(self, config: dict[str, Any]) -> Any:
        class Snapshot:
            def __init__(self, values: dict[str, Any] | None) -> None:
                self.values = values

        thread_id = config["configurable"]["thread_id"]
        return Snapshot(self._states.get(thread_id))

    def update_state(self, config: dict[str, Any], values: dict[str, Any]) -> Any:
        thread_id = config["configurable"]["thread_id"]
        if thread_id not in self._states:
            self._states[thread_id] = {}

        # Emulate LangGraph's add_messages reducer for the messages key.
        if "messages" in values:
            incoming = list(values["messages"])
            if any(
                isinstance(message, RemoveMessage) and message.id == REMOVE_ALL_MESSAGES
                for message in incoming
            ):
                self._states[thread_id]["messages"] = []
            else:
                existing = list(self._states[thread_id].get("messages", []))
                self._states[thread_id]["messages"] = existing + incoming

        # Merge scalar updates.
        for key, value in values.items():
            if key != "messages":
                self._states[thread_id][key] = value


@pytest.fixture
def store() -> HistoryStore:
    return HistoryStore(FakeGraph(), max_history_messages=10, redaction_enabled=True)


class TestSessionIsolation:
    def test_messages_from_one_session_not_visible_to_another(self, store: HistoryStore) -> None:
        store.add_user_message("session-a", "hello")
        store.add_user_message("session-b", "goodbye")

        history_a = store.get_history("session-a")
        history_b = store.get_history("session-b")

        assert len(history_a) == 1
        assert history_a[0]["content"] == "hello"
        assert len(history_b) == 1
        assert history_b[0]["content"] == "goodbye"

    def test_history_for_unknown_session_is_empty(self, store: HistoryStore) -> None:
        assert store.get_history("unknown-session") == []


class TestResetSession:
    def test_reset_clears_messages_and_state(self, store: HistoryStore) -> None:
        store.add_user_message("session-a", "hello")
        store.add_assistant_message("session-a", "hi there")
        store.reset_session("session-a")

        assert store.get_history("session-a") == []
        # After reset the checkpoint still exists but is in the initial state,
        # so authentication/identification data and messages must be gone.
        snapshot = store._graph.get_state(store._config("session-a"))
        assert snapshot.values is not None
        assert snapshot.values.get("messages") == []
        assert snapshot.values.get("matched_customer_id") is None
        assert snapshot.values.get("status") == "collecting"


class TestAddMessages:
    def test_add_user_message_then_assistant(self, store: HistoryStore) -> None:
        store.add_user_message("session-a", "I need help")
        store.add_assistant_message("session-a", "Sure, with what?")

        history = store.get_history("session-a")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_user_message_is_redacted(self, store: HistoryStore) -> None:
        store.add_user_message("session-a", "My name is Lisa", sensitive_values={"Lisa"})
        history = store.get_history("session-a")
        assert "Lisa" not in history[0]["content"]
        assert "[REDACTED]" in history[0]["content"]


class TestTruncation:
    def test_history_truncated_to_max_messages(self, store: HistoryStore) -> None:
        for i in range(12):
            store.add_user_message("session-a", f"message {i}")
        history = store.get_history("session-a", max_messages=3)
        assert len(history) == 3
        assert history[-1]["content"] == "message 11"


class TestRedaction:
    def test_iban_redacted_in_user_message(self, store: HistoryStore) -> None:
        store.add_user_message("session-a", "My IBAN is DE89370400440532013000")
        history = store.get_history("session-a")
        assert "DE89370400440532013000" not in history[0]["content"]
        assert "[REDACTED]" in history[0]["content"]

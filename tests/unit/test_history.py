"""Unit tests for conversation history manipulation helpers."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from healthcare_support.core.history import (
    redact_message,
    redact_sensitive_values,
    sanitize_history,
    truncate_history,
)


class TestSanitizeHistory:
    def test_includes_human_and_ai_messages(self) -> None:
        messages = [
            HumanMessage(content="hello"),
            AIMessage(content="hi"),
        ]
        result = sanitize_history(messages)
        assert result == [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

    def test_excludes_system_and_tool_messages(self) -> None:
        messages = [
            HumanMessage(content="hello"),
            SystemMessage(content="system prompt"),
            AIMessage(content="hi"),
        ]
        result = sanitize_history(messages)
        assert result == [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]

    def test_truncates_to_recent_messages(self) -> None:
        messages = [
            HumanMessage(content="one"),
            AIMessage(content="two"),
            HumanMessage(content="three"),
            AIMessage(content="four"),
        ]
        result = sanitize_history(messages, max_messages=2)
        assert result == [
            {"role": "user", "content": "three"},
            {"role": "assistant", "content": "four"},
        ]

    def test_zero_limit_returns_empty(self) -> None:
        messages = [HumanMessage(content="hello")]
        assert sanitize_history(messages, max_messages=0) == []


class TestTruncateHistory:
    def test_keeps_most_recent(self) -> None:
        history = [
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
            {"role": "user", "content": "three"},
        ]
        assert truncate_history(history, 1) == [{"role": "user", "content": "three"}]


class TestRedactSensitiveValues:
    def test_redacts_known_values(self) -> None:
        text = "My name is Lisa and my phone is +14155552671"
        result = redact_sensitive_values(text, {"Lisa", "+14155552671"})
        assert "Lisa" not in result
        assert "+14155552671" not in result
        assert "[REDACTED]" in result

    def test_longer_values_take_precedence(self) -> None:
        text = "Lisa Silva is the name"
        result = redact_sensitive_values(text, {"Lisa", "Lisa Silva"})
        assert result == "[REDACTED] is the name"


class TestRedactMessage:
    def test_redacts_known_values_and_patterns(self) -> None:
        text = "date of birth 1990-01-15 and phone +14155552671"
        result = redact_message(text, {"Lisa"})
        assert "1990-01-15" not in result
        assert "+14155552671" not in result

    def test_redacts_secret_answer(self) -> None:
        result = redact_message("The answer is Yoda", {"Yoda"})
        assert "Yoda" not in result
        assert "[REDACTED]" in result

    def test_respects_redaction_flag(self) -> None:
        text = "My name is Lisa"
        result = redact_message(text, {"Lisa"}, enable_patterns=False)
        assert "Lisa" not in result
        assert "[REDACTED]" in result

    def test_pattern_redaction_does_not_over_redact(self) -> None:
        # Simple short digit strings should not be redacted as phone numbers.
        result = redact_message("I have 2 accounts")
        assert result == "I have 2 accounts"

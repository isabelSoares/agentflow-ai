"""Unit tests for observability: redaction and audit events (FR-015, Principle VI)."""

from __future__ import annotations

import logging

from banking_support.data.seed import CUSTOMERS
from banking_support.observability.audit import AuditEvent, build_audit_event
from banking_support.observability.logging import _JsonFormatter, redact


class TestRedaction:
    def test_redacts_iban(self) -> None:
        text = f"My IBAN is {CUSTOMERS[0].iban}."
        assert redact(text) == "My IBAN is [REDACTED]."

    def test_redacts_phone(self) -> None:
        text = f"Call me at {CUSTOMERS[0].phone}."
        assert redact(text) == "Call me at [REDACTED]."

    def test_redacts_api_key(self) -> None:
        text = "Provider rejected key gsk_abcdefghijklmnop"
        assert redact(text) == "Provider rejected key [REDACTED]"

    def test_leaves_other_text(self) -> None:
        assert redact("Hello world") == "Hello world"


class TestJsonFormatterRedaction:
    def test_formatter_redacts_message_values(self) -> None:
        record = logging.LogRecord(
            name="banking_support.test",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="Call %s with key %s",
            args=(CUSTOMERS[0].phone, "gsk_abcdefghijklmnop"),
            exc_info=None,
        )

        output = _JsonFormatter().format(record)

        assert CUSTOMERS[0].phone not in output
        assert "gsk_abcdefghijklmnop" not in output
        assert "[REDACTED]" in output


class TestAuditEvent:
    def test_event_has_no_secret_or_attribute_values(self) -> None:
        event = AuditEvent(
            event_type="auth_success",
            conversation_id="conv-1",
            identified=True,
            authenticated=True,
        )
        data = event.__dict__
        assert "secret_answer" not in data
        assert "phone" not in data
        assert "iban" not in data
        assert data["authenticated"] is True

    def test_builder_drops_fields_outside_safe_allowlist(self) -> None:
        event = build_audit_event(
            "identified",
            "conv-1",
            identified=True,
            phone="+49123456789",
            iban="DE89370400440532013000",
            secret_answer="yoda",
            raw_message="my private message",
        )

        assert event.identified is True
        assert "phone" not in event.__dict__
        assert "iban" not in event.__dict__
        assert "secret_answer" not in event.__dict__
        assert "raw_message" not in event.__dict__

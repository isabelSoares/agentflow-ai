"""Tests for privacy-safe operation tracing."""

from __future__ import annotations

from contextlib import suppress

from banking_support.observability.tracing import ListTraceRecorder, record_operation


def test_trace_records_safe_operation_metadata() -> None:
    recorder = ListTraceRecorder()

    result, record = record_operation(
        "llm.extraction",
        lambda: "structured-result",
        recorder=recorder,
        provider="test-provider",
        model="test-model",
        retry_count=1,
    )

    assert result == "structured-result"
    assert record.operation == "llm.extraction"
    assert record.outcome == "success"
    assert record.duration_ms >= 0
    assert record.provider == "test-provider"
    assert record.retry_count == 1
    assert recorder.records == [record]


def test_trace_records_error_class_without_error_payload() -> None:
    recorder = ListTraceRecorder()

    with suppress(ValueError):
        record_operation(
            "voice.stt", lambda: (_ for _ in ()).throw(ValueError("secret")), recorder=recorder
        )

    assert recorder.records[0].outcome == "error"
    assert recorder.records[0].error_class == "ValueError"

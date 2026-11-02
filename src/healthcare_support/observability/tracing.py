"""Privacy-first operation tracing with an optional OpenTelemetry bridge."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

logger = logging.getLogger("healthcare_support.trace")


@dataclass(frozen=True)
class TraceRecord:
    """Redacted metadata for one external or workflow operation."""

    operation: str
    outcome: str
    duration_ms: float
    provider: str | None = None
    model: str | None = None
    token_usage: dict[str, int] = field(default_factory=dict)
    retry_count: int = 0
    error_class: str | None = None


class TraceRecorder(Protocol):
    """Sink for already-redacted operation records."""

    def record(self, record: TraceRecord) -> None: ...


class LoggingTraceRecorder:
    """Emit only the safe TraceRecord fields to the structured logger."""

    def record(self, record: TraceRecord) -> None:
        logger.info("operation_trace %s", record)


class ListTraceRecorder:
    """Small in-memory recorder for deterministic tests."""

    def __init__(self) -> None:
        self.records: list[TraceRecord] = []

    def record(self, record: TraceRecord) -> None:
        self.records.append(record)


def _otel_span(operation: str, attributes: dict[str, Any]) -> Any:
    """Start an optional OpenTelemetry span without making telemetry a hard dependency."""
    try:
        from opentelemetry import trace

        return trace.get_tracer("healthcare_support").start_as_current_span(
            operation, attributes=attributes
        )
    except ImportError:
        from contextlib import nullcontext

        return nullcontext()


def record_operation(
    operation: str,
    action: Any,
    *,
    recorder: TraceRecorder | None = None,
    provider: str | None = None,
    model: str | None = None,
    retry_count: int = 0,
    token_usage_from_result: Callable[[Any], dict[str, int]] | None = None,
) -> tuple[Any, TraceRecord]:
    """Run an operation and publish only redacted timing/outcome metadata."""
    started = perf_counter()
    outcome = "success"
    error_class: str | None = None
    result: Any = None
    try:
        with _otel_span(operation, {"provider": provider or "", "model": model or ""}):
            result = action()
    except Exception as exc:
        outcome = "error"
        error_class = type(exc).__name__
        raise
    finally:
        record = TraceRecord(
            operation=operation,
            outcome=outcome,
            duration_ms=round((perf_counter() - started) * 1000, 3),
            provider=provider,
            model=model,
            token_usage=(token_usage_from_result(result) if token_usage_from_result else {}),
            retry_count=retry_count,
            error_class=error_class,
        )
        (recorder or LoggingTraceRecorder()).record(record)
    return result, record


__all__ = [
    "ListTraceRecorder",
    "LoggingTraceRecorder",
    "TraceRecord",
    "TraceRecorder",
    "record_operation",
]

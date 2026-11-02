"""Timeout and retry policy for synchronous provider adapters."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from time import sleep
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ExternalCallPolicy:
    timeout_seconds: float = 10.0
    max_retries: int = 1
    backoff_seconds: float = 0.1
    idempotent: bool = True

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0 or self.timeout_seconds > 120:
            raise ValueError("timeout_seconds must be greater than zero and at most 120")
        if self.max_retries < 0 or self.max_retries > 3:
            raise ValueError("max_retries must be between 0 and 3")
        if self.backoff_seconds < 0 or self.backoff_seconds > 5:
            raise ValueError("backoff_seconds must be between 0 and 5")
        if not self.idempotent and self.max_retries:
            raise ValueError("non-idempotent calls cannot be retried")


def _retryable(exc: BaseException) -> bool:
    """Retry transport/server failures, never validation or authentication errors."""
    status_code = getattr(exc, "status_code", None)
    if status_code == 429 or isinstance(status_code, int) and 500 <= status_code <= 599:
        return True
    name = type(exc).__name__.casefold()
    text = str(exc).casefold()
    return any(
        token in name or token in text
        for token in ("timeout", "connection", "429", "rate limit", "503", "502", "504")
    )


def call_with_policy[T](
    operation: Callable[[], T],
    policy: ExternalCallPolicy,
    fallback: T,
) -> T:
    """Run a provider call with a hard caller deadline and bounded safe fallback."""
    attempts = policy.max_retries + 1
    for attempt in range(attempts):
        try:
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(operation)
            try:
                return future.result(timeout=policy.timeout_seconds)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        except Exception as exc:
            if attempt + 1 >= attempts or not _retryable(exc):
                return fallback
            if policy.backoff_seconds:
                sleep(policy.backoff_seconds * (attempt + 1))
    return fallback


__all__ = ["ExternalCallPolicy", "call_with_policy"]

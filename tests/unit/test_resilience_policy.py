"""Offline tests for bounded provider execution."""

from time import monotonic, sleep

from healthcare_support.resilience.policy import ExternalCallPolicy, call_with_policy


def test_timeout_returns_fallback_within_bound() -> None:
    started = monotonic()
    result = call_with_policy(
        lambda: sleep(0.2),
        ExternalCallPolicy(timeout_seconds=0.01, max_retries=0),
        fallback="safe",
    )

    assert result == "safe"
    assert monotonic() - started < 0.1


def test_transient_failure_is_retried_once() -> None:
    attempts = 0

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("provider unavailable")
        return "ok"

    assert call_with_policy(operation, ExternalCallPolicy(backoff_seconds=0), "safe") == "ok"
    assert attempts == 2


def test_non_idempotent_policy_rejects_retries() -> None:
    try:
        ExternalCallPolicy(max_retries=1, idempotent=False)
    except ValueError:
        pass
    else:
        raise AssertionError("non-idempotent operations must not retry")

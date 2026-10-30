"""Secret-answer verification and attempt-limit enforcement.

All decisions here are deterministic and do not use an LLM.
"""

from __future__ import annotations

from banking_support.core.normalization import normalize_answer
from banking_support.core.responses import (
    AUTHENTICATED_CONFIRMATION,
    TERMINATION_GENERIC,
    WRONG_SECRET_ANSWER,
)
from banking_support.domain.conversation import TerminationReason
from banking_support.domain.customer import Customer

MAX_ATTEMPTS = 3


def check_secret_answer(provided: str | None, customer: Customer) -> bool:
    """True when the normalized provided answer matches the registered answer."""
    if provided is None:
        return False
    return normalize_answer(provided) == normalize_answer(customer.secret_answer)


class VerificationResult:
    """Result of processing a secret-answer attempt."""

    def __init__(
        self,
        authenticated: bool,
        terminated: bool,
        reply: str,
        termination_reason: str | None = None,
    ) -> None:
        self.authenticated = authenticated
        self.terminated = terminated
        self.reply = reply
        self.termination_reason = termination_reason


def process_secret_attempt(
    provided: str | None,
    customer: Customer,
    attempts_so_far: int,
) -> VerificationResult:
    """Evaluate one secret-answer attempt, applying the 3-attempt limit.

    Returns the new terminal state and the reply to send.
    """
    if check_secret_answer(provided, customer):
        return VerificationResult(
            authenticated=True,
            terminated=False,
            reply=AUTHENTICATED_CONFIRMATION,
        )

    new_attempts = attempts_so_far + 1
    if new_attempts >= MAX_ATTEMPTS:
        return VerificationResult(
            authenticated=False,
            terminated=True,
            reply=TERMINATION_GENERIC,
            termination_reason=TerminationReason.SECRET_EXHAUSTED.value,
        )
    return VerificationResult(
        authenticated=False,
        terminated=False,
        reply=WRONG_SECRET_ANSWER,
    )


def process_identification_failure(attempts_so_far: int) -> VerificationResult:
    """Handle a failed identification evaluation, applying the 3-attempt limit."""
    from banking_support.core.responses import (  # local import to avoid cycles
        IDENTIFICATION_FAILURE,
        TERMINATION_NON_CLIENT,
    )

    new_attempts = attempts_so_far + 1
    if new_attempts >= MAX_ATTEMPTS:
        return VerificationResult(
            authenticated=False,
            terminated=True,
            reply=TERMINATION_NON_CLIENT,
            termination_reason=TerminationReason.IDENTIFICATION_EXHAUSTED.value,
        )
    return VerificationResult(
        authenticated=False,
        terminated=False,
        reply=IDENTIFICATION_FAILURE,
    )


__all__ = [
    "check_secret_answer",
    "process_secret_attempt",
    "process_identification_failure",
    "VerificationResult",
    "MAX_ATTEMPTS",
]

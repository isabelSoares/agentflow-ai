"""Deterministic customer classification logic for the Bouncer Agent.

This module contains no LLM imports and no orchestration dependencies. All
classification decisions are reproducible pure functions of the inputs.
"""

from __future__ import annotations

from banking_support.domain.conversation import CustomerClassification
from banking_support.domain.customer import Customer


class ClassificationError(Exception):
    """Raised when classification cannot be performed safely."""


class UnverifiedError(ClassificationError):
    """Raised when classification is requested before successful verification."""


def classify_customer(
    customer: Customer | None,
    *,
    is_verified: bool,
) -> CustomerClassification:
    """Classify a caller based on trusted account data.

    Args:
        customer: The authorized customer record, or ``None`` if no record was found.
        is_verified: Whether the Greeter Agent has successfully verified the caller.

    Returns:
        ``PREMIUM`` for verified customers with ``is_premium=True``,
        ``REGULAR`` for verified active customers without premium membership,
        ``NON_CUSTOMER`` when no customer relationship can be confirmed.

    Raises:
        UnverifiedError: If ``is_verified`` is false.
    """
    if not is_verified:
        raise UnverifiedError("Classification requires successful identity verification.")

    if customer is None:
        return CustomerClassification.NON_CUSTOMER

    if customer.is_premium:
        return CustomerClassification.PREMIUM

    return CustomerClassification.REGULAR

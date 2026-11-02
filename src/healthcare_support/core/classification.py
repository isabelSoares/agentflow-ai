"""Deterministic patient classification logic for the Bouncer Agent.

This module contains no LLM imports and no orchestration dependencies. All
classification decisions are reproducible pure functions of the inputs.
"""

from __future__ import annotations

from healthcare_support.domain.conversation import PatientClassification
from healthcare_support.domain.patient import Patient


class ClassificationError(Exception):
    """Raised when classification cannot be performed safely."""


class UnverifiedError(ClassificationError):
    """Raised when classification is requested before successful verification."""


def classify_patient(
    patient: Patient | None,
    *,
    is_verified: bool,
) -> PatientClassification:
    """Classify a caller based on trusted account data.

    Args:
        patient: The authorized patient record, or ``None`` if no record was found.
        is_verified: Whether the Greeter Agent has successfully verified the caller.

    Returns:
        ``PREMIUM`` for verified patients with ``is_premium=True``,
        ``REGULAR`` for verified active patients without premium membership,
        ``NON_PATIENT`` when no patient relationship can be confirmed.

    Raises:
        UnverifiedError: If ``is_verified`` is false.
    """
    if not is_verified:
        raise UnverifiedError("Classification requires successful identity verification.")

    if patient is None:
        return PatientClassification.NON_PATIENT

    if patient.is_premium:
        return PatientClassification.PREMIUM

    return PatientClassification.REGULAR

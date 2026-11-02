"""Unit tests for deterministic patient classification."""

from __future__ import annotations

import pytest

from healthcare_support.core.classification import (
    ClassificationError,
    UnverifiedError,
    classify_patient,
)
from healthcare_support.domain.conversation import PatientClassification
from healthcare_support.domain.patient import Patient


@pytest.fixture
def premium_patient() -> Patient:
    return Patient(
        id="cust-premium",
        name="Premium User",
        phone="+14155552671",
        date_of_birth="1990-01-15",
        secret_question="Pet?",
        secret_answer="Yoda",
        is_premium=True,
    )


@pytest.fixture
def regular_patient() -> Patient:
    return Patient(
        id="cust-regular",
        name="Regular User",
        phone="+12025550123",
        date_of_birth="1978-11-03",
        secret_question="Color?",
        secret_answer="Blue",
        is_premium=False,
    )


class TestClassifyPatient:
    def test_verified_premium_patient(self, premium_patient: Patient) -> None:
        result = classify_patient(premium_patient, is_verified=True)
        assert result == PatientClassification.PREMIUM

    def test_verified_regular_patient(self, regular_patient: Patient) -> None:
        result = classify_patient(regular_patient, is_verified=True)
        assert result == PatientClassification.REGULAR

    def test_verified_patient_with_missing_premium_flag_is_regular(
        self, regular_patient: Patient
    ) -> None:
        # Explicitly assert the default behavior: missing/False premium flag → regular.
        assert regular_patient.is_premium is False
        result = classify_patient(regular_patient, is_verified=True)
        assert result == PatientClassification.REGULAR

    def test_verified_missing_patient_is_non_patient(self) -> None:
        result = classify_patient(None, is_verified=True)
        assert result == PatientClassification.NON_PATIENT

    def test_unverified_patient_raises(self, premium_patient: Patient) -> None:
        with pytest.raises(UnverifiedError):
            classify_patient(premium_patient, is_verified=False)

    def test_unverified_none_patient_raises(self) -> None:
        with pytest.raises(UnverifiedError):
            classify_patient(None, is_verified=False)

    def test_classification_error_is_a_classification_error(self, premium_patient: Patient) -> None:
        with pytest.raises(ClassificationError):
            classify_patient(premium_patient, is_verified=False)

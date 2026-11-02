"""In-memory patient repository implementation."""

from __future__ import annotations

from collections.abc import Sequence

from healthcare_support.data.repository import PatientRepository
from healthcare_support.data.seed import PATIENTS
from healthcare_support.domain.patient import Patient


class InMemoryPatientRepository(PatientRepository):
    """Thread-safe enough for the demo: immutable seed data, read-only access."""

    def __init__(self, patients: Sequence[Patient] | None = None) -> None:
        self._patients: tuple[Patient, ...] = tuple(patients or PATIENTS)

    def list_all(self) -> Sequence[Patient]:
        return self._patients

    def get_by_id(self, patient_id: str) -> Patient | None:
        for patient in self._patients:
            if patient.id == patient_id:
                return patient
        return None

"""Patient data access layer."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from healthcare_support.domain.patient import Patient


class PatientRepository(Protocol):
    """Protocol for patient data access.

    Business logic in `core/` performs its own matching on the returned records so
    that verification decisions remain deterministic and testable.
    """

    def list_all(self) -> Sequence[Patient]: ...

    def get_by_id(self, patient_id: str) -> Patient | None: ...

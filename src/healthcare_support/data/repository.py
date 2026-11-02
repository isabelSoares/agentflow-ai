"""Customer data access layer."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from healthcare_support.domain.customer import Customer


class CustomerRepository(Protocol):
    """Protocol for customer data access.

    Business logic in `core/` performs its own matching on the returned records so
    that verification decisions remain deterministic and testable.
    """

    def list_all(self) -> Sequence[Customer]: ...

    def get_by_id(self, customer_id: str) -> Customer | None: ...

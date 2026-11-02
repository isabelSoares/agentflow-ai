"""In-memory customer repository implementation."""

from __future__ import annotations

from collections.abc import Sequence

from healthcare_support.data.repository import CustomerRepository
from healthcare_support.data.seed import CUSTOMERS
from healthcare_support.domain.customer import Customer


class InMemoryCustomerRepository(CustomerRepository):
    """Thread-safe enough for the demo: immutable seed data, read-only access."""

    def __init__(self, customers: Sequence[Customer] | None = None) -> None:
        self._customers: tuple[Customer, ...] = tuple(customers or CUSTOMERS)

    def list_all(self) -> Sequence[Customer]:
        return self._customers

    def get_by_id(self, customer_id: str) -> Customer | None:
        for customer in self._customers:
            if customer.id == customer_id:
                return customer
        return None

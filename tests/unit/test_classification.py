"""Unit tests for deterministic customer classification."""

from __future__ import annotations

import pytest

from healthcare_support.core.classification import (
    ClassificationError,
    UnverifiedError,
    classify_customer,
)
from healthcare_support.domain.conversation import CustomerClassification
from healthcare_support.domain.customer import Customer


@pytest.fixture
def premium_customer() -> Customer:
    return Customer(
        id="cust-premium",
        name="Premium User",
        phone="+14155552671",
        iban="DE89370400440532013000",
        secret_question="Pet?",
        secret_answer="Yoda",
        is_premium=True,
    )


@pytest.fixture
def regular_customer() -> Customer:
    return Customer(
        id="cust-regular",
        name="Regular User",
        phone="+12025550123",
        iban="GB33BUKB20201555555555",
        secret_question="Color?",
        secret_answer="Blue",
        is_premium=False,
    )


class TestClassifyCustomer:
    def test_verified_premium_customer(self, premium_customer: Customer) -> None:
        result = classify_customer(premium_customer, is_verified=True)
        assert result == CustomerClassification.PREMIUM

    def test_verified_regular_customer(self, regular_customer: Customer) -> None:
        result = classify_customer(regular_customer, is_verified=True)
        assert result == CustomerClassification.REGULAR

    def test_verified_customer_with_missing_premium_flag_is_regular(
        self, regular_customer: Customer
    ) -> None:
        # Explicitly assert the default behavior: missing/False premium flag → regular.
        assert regular_customer.is_premium is False
        result = classify_customer(regular_customer, is_verified=True)
        assert result == CustomerClassification.REGULAR

    def test_verified_missing_customer_is_non_customer(self) -> None:
        result = classify_customer(None, is_verified=True)
        assert result == CustomerClassification.NON_CUSTOMER

    def test_unverified_customer_raises(self, premium_customer: Customer) -> None:
        with pytest.raises(UnverifiedError):
            classify_customer(premium_customer, is_verified=False)

    def test_unverified_none_customer_raises(self) -> None:
        with pytest.raises(UnverifiedError):
            classify_customer(None, is_verified=False)

    def test_classification_error_is_a_classification_error(
        self, premium_customer: Customer
    ) -> None:
        with pytest.raises(ClassificationError):
            classify_customer(premium_customer, is_verified=False)

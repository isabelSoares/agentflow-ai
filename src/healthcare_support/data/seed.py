"""Seed dataset for the identity-verification feature."""

from __future__ import annotations

from healthcare_support.domain.customer import Customer

CUSTOMERS: list[Customer] = [
    Customer(
        id="cust-1",
        name="Lisa",
        phone="+14155552671",
        iban="DE89370400440532013000",
        secret_question="Which is the name of my dog?",
        secret_answer="Yoda",
        is_premium=True,
    ),
    # Two customers sharing a phone number to exercise ambiguous-match logic.
    Customer(
        id="cust-2",
        name="Maria Silva",
        phone="+351912345678",
        iban="PT50000201230000000001087",
        secret_question="What is your mother's maiden name?",
        secret_answer="Santos",
    ),
    Customer(
        id="cust-3",
        name="Maria Souza",
        phone="+351912345678",
        iban="PT50000201230000000001184",
        secret_question="What was your first car?",
        secret_answer="Gol",
    ),
    Customer(
        id="cust-4",
        name="John Doe",
        phone="+12025550123",
        iban="GB33BUKB20201555555555",
        secret_question="What is your favorite color?",
        secret_answer="Blue",
    ),
]

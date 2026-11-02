"""Seed dataset for the identity-verification feature."""

from __future__ import annotations

from healthcare_support.domain.patient import Patient

PATIENTS: list[Patient] = [
    Patient(
        id="cust-1",
        name="Lisa",
        phone="+14155552671",
        date_of_birth="1990-01-15",
        secret_question="Which is the name of my dog?",
        secret_answer="Yoda",
        is_premium=True,
    ),
    # Two patients sharing a phone number to exercise ambiguous-match logic.
    Patient(
        id="cust-2",
        name="Maria Silva",
        phone="+351912345678",
        date_of_birth="1985-07-22",
        secret_question="What is your mother's maiden name?",
        secret_answer="Santos",
    ),
    Patient(
        id="cust-3",
        name="Maria Souza",
        phone="+351912345678",
        date_of_birth="1987-03-12",
        secret_question="What was your first car?",
        secret_answer="Gol",
    ),
    Patient(
        id="cust-4",
        name="John Doe",
        phone="+12025550123",
        date_of_birth="1978-11-03",
        secret_question="What is your favorite color?",
        secret_answer="Blue",
    ),
]

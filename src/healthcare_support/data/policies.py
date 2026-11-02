"""Trusted healthcare policy rules consumed by the Guardrails component.

Guardrails enforces these rules but does not invent, modify, or persist them.
"""

from __future__ import annotations

from healthcare_support.domain.conversation import PatientClassification
from healthcare_support.domain.guardrails import HealthcarePolicyRule

_ALL_PATIENTS = frozenset({PatientClassification.PREMIUM, PatientClassification.REGULAR})


def default_healthcare_policy() -> dict[str, HealthcarePolicyRule]:
    """Return the trusted healthcare policy configuration."""
    return {
        "appointment_request": HealthcarePolicyRule(
            action_type="appointment_request",
            allowed_tiers=_ALL_PATIENTS,
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_availability", "confirmation"}
            ),
        ),
        "insurance_request": HealthcarePolicyRule(
            action_type="insurance_request",
            allowed_tiers=_ALL_PATIENTS,
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_coverage", "guaranteed_reimbursement"}
            ),
        ),
        "specialist_referral": HealthcarePolicyRule(
            action_type="specialist_referral",
            allowed_tiers=_ALL_PATIENTS,
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_availability", "confirmation"}
            ),
        ),
        "prescription_request": HealthcarePolicyRule(
            action_type="prescription_request",
            allowed_tiers=_ALL_PATIENTS,
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_availability", "confirmation"}
            ),
        ),
        "record_modification": HealthcarePolicyRule(
            action_type="record_modification",
            allowed_tiers=_ALL_PATIENTS,
            requires_authentication=True,
            allow_routing_as_inquiry=False,
            prohibited_commitments=frozenset({"completion", "approval"}),
        ),
        "billing_inquiry": HealthcarePolicyRule(
            action_type="billing_inquiry",
            allowed_tiers=_ALL_PATIENTS,
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(),
        ),
        "general_inquiry": HealthcarePolicyRule(
            action_type="general_inquiry",
            allowed_tiers=frozenset(
                {
                    PatientClassification.PREMIUM,
                    PatientClassification.REGULAR,
                    PatientClassification.NON_PATIENT,
                }
            ),
            requires_authentication=False,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(),
        ),
        "premium_healthcare": HealthcarePolicyRule(
            action_type="premium_healthcare",
            allowed_tiers=frozenset({PatientClassification.PREMIUM}),
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(),
        ),
    }


__all__ = ["default_healthcare_policy"]

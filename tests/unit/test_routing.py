"""Unit tests for deterministic support routing."""

from __future__ import annotations

import pytest

from healthcare_support.core.routing import (
    authentication_gate,
    route_support_request,
    tier_key,
)
from healthcare_support.data.support_directory import default_support_directory
from healthcare_support.domain.conversation import PatientClassification
from healthcare_support.domain.routing import (
    IntentClassification,
    RoutingStatus,
    SupportDepartment,
    SupportDirectory,
    SupportIntent,
)


@pytest.fixture
def directory() -> SupportDirectory:
    return default_support_directory()


class TestPremiumRouting:
    def test_premium_appointment_assistance_routes_to_premium_support(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.PREMIUM,
            intent_classification=IntentClassification(intent=SupportIntent.APPOINTMENT_ASSISTANCE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.ROUTED
        assert decision.intent == SupportIntent.APPOINTMENT_ASSISTANCE
        assert decision.department_key == "premium_support"
        assert decision.contact == "+1999888999"
        assert "Premium Patient Support" in decision.message

    def test_tier_helper_uses_only_trusted_classifications(self) -> None:
        assert tier_key(PatientClassification.PREMIUM) == "premium_support"
        assert tier_key(PatientClassification.REGULAR) == "standard_support"

    def test_authentication_gate_blocks_before_directory_lookup(self) -> None:
        decision = authentication_gate(
            is_authenticated=False,
            patient_classification=PatientClassification.PREMIUM,
            intent=SupportIntent.APPOINTMENT_ASSISTANCE,
        )
        assert decision is not None
        assert decision.status == RoutingStatus.BLOCKED

    def test_premium_general_healthcare_routes_to_premium_support(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.PREMIUM,
            intent_classification=IntentClassification(intent=SupportIntent.GENERAL_HEALTHCARE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.ROUTED
        assert decision.department_key == "premium_support"

    def test_premium_specialist_referral_routes_to_insurance_billing(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.PREMIUM,
            intent_classification=IntentClassification(intent=SupportIntent.SPECIALIST_REFERRAL),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.ROUTED
        assert decision.intent == SupportIntent.SPECIALIST_REFERRAL
        assert decision.department_key == "insurance_billing"
        assert decision.contact == "+18005551234"


class TestRegularRouting:
    def test_regular_appointment_assistance_routes_to_standard_support(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(intent=SupportIntent.APPOINTMENT_ASSISTANCE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.ROUTED
        assert decision.department_key == "standard_support"
        assert decision.contact == "+1112112112"

    def test_regular_specialist_referral_routes_to_insurance_billing(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(intent=SupportIntent.SPECIALIST_REFERRAL),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.ROUTED
        assert decision.department_key == "insurance_billing"


class TestSpecialistPrecedence:
    def test_specialist_takes_precedence_over_premium_tier(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.PREMIUM,
            intent_classification=IntentClassification(
                intent=SupportIntent.OTHER_SPECIALIZED,
                specialization="specialist_referral",
            ),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.ROUTED
        assert decision.department_key == "insurance_billing"


class TestClarificationAndFallback:
    def test_ambiguous_request_returns_clarification(self, directory: SupportDirectory) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(
                intent=SupportIntent.AMBIGUOUS,
                needs_clarification=True,
                clarification_prompt="Could you clarify what you need?",
            ),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.CLARIFICATION_REQUIRED
        assert decision.department_key is None
        assert "Could you clarify" in decision.message

    def test_unsupported_request_returns_fallback(self, directory: SupportDirectory) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(intent=SupportIntent.UNSUPPORTED),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.FALLBACK
        assert decision.department_key is None
        assert decision.contact is None

    def test_uninterpretable_request_returns_fallback(self, directory: SupportDirectory) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(intent=SupportIntent.UNINTERPRETABLE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.FALLBACK


class TestAuthorizationAndClassificationBoundaries:
    def test_unauthenticated_request_is_blocked(self, directory: SupportDirectory) -> None:
        decision = route_support_request(
            is_authenticated=False,
            patient_classification=PatientClassification.PREMIUM,
            intent_classification=IntentClassification(intent=SupportIntent.APPOINTMENT_ASSISTANCE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.BLOCKED
        assert decision.department_key is None

    def test_missing_classification_is_blocked(self, directory: SupportDirectory) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=None,
            intent_classification=IntentClassification(intent=SupportIntent.APPOINTMENT_ASSISTANCE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.BLOCKED

    def test_non_patient_is_fallback(self, directory: SupportDirectory) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.NON_PATIENT,
            intent_classification=IntentClassification(intent=SupportIntent.APPOINTMENT_ASSISTANCE),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.FALLBACK
        assert decision.department_key is None


class TestDepartmentAvailability:
    def test_unavailable_specialist_returns_fallback(self) -> None:
        directory = SupportDirectory(
            departments={
                "standard_support": SupportDepartment(
                    key="standard_support",
                    display_name="Standard Patient Support",
                    available=True,
                ),
                "insurance_billing": SupportDepartment(
                    key="insurance_billing",
                    display_name="Insurance and Billing",
                    specializations={"specialist_referral"},
                    available=False,
                ),
            }
        )
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.PREMIUM,
            intent_classification=IntentClassification(intent=SupportIntent.SPECIALIST_REFERRAL),
            support_directory=directory,
        )
        assert decision.status == RoutingStatus.FALLBACK
        assert decision.department_key is None

    def test_missing_standard_support_returns_fallback(self, directory: SupportDirectory) -> None:
        directory_without_standard = SupportDirectory(
            departments={k: v for k, v in directory.departments.items() if k != "standard_support"}
        )
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(intent=SupportIntent.APPOINTMENT_ASSISTANCE),
            support_directory=directory_without_standard,
        )
        assert decision.status == RoutingStatus.FALLBACK


class TestNoInvention:
    def test_fallback_does_not_invent_department_or_contact(
        self, directory: SupportDirectory
    ) -> None:
        decision = route_support_request(
            is_authenticated=True,
            patient_classification=PatientClassification.REGULAR,
            intent_classification=IntentClassification(intent=SupportIntent.UNSUPPORTED),
            support_directory=directory,
        )
        assert decision.department_key is None
        assert decision.department_name is None
        assert decision.contact is None
        assert "+" not in (decision.message or "")

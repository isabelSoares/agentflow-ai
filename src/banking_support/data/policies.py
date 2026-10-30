"""Trusted banking policy rules consumed by the Guardrails component.

Guardrails enforces these rules but does not invent, modify, or persist them.
"""

from __future__ import annotations

from banking_support.domain.conversation import CustomerClassification
from banking_support.domain.guardrails import BankingPolicyRule


def default_banking_policy() -> dict[str, BankingPolicyRule]:
    """Return the trusted banking policy configuration."""
    return {
        "loan_request": BankingPolicyRule(
            action_type="loan_request",
            allowed_tiers=frozenset(
                {CustomerClassification.PREMIUM, CustomerClassification.REGULAR}
            ),
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_rate", "guaranteed_eligibility"}
            ),
        ),
        "credit_card_request": BankingPolicyRule(
            action_type="credit_card_request",
            allowed_tiers=frozenset(
                {CustomerClassification.PREMIUM, CustomerClassification.REGULAR}
            ),
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_rate", "guaranteed_eligibility"}
            ),
        ),
        "insurance_request": BankingPolicyRule(
            action_type="insurance_request",
            allowed_tiers=frozenset(
                {CustomerClassification.PREMIUM, CustomerClassification.REGULAR}
            ),
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(
                {"approval", "guaranteed_rate", "guaranteed_eligibility"}
            ),
        ),
        "fund_transfer": BankingPolicyRule(
            action_type="fund_transfer",
            allowed_tiers=frozenset(
                {CustomerClassification.PREMIUM, CustomerClassification.REGULAR}
            ),
            requires_authentication=True,
            allow_routing_as_inquiry=False,
            prohibited_commitments=frozenset({"completion", "approval"}),
        ),
        "account_modification": BankingPolicyRule(
            action_type="account_modification",
            allowed_tiers=frozenset(
                {CustomerClassification.PREMIUM, CustomerClassification.REGULAR}
            ),
            requires_authentication=True,
            allow_routing_as_inquiry=False,
            prohibited_commitments=frozenset({"completion", "approval"}),
        ),
        "balance_inquiry": BankingPolicyRule(
            action_type="balance_inquiry",
            allowed_tiers=frozenset(
                {CustomerClassification.PREMIUM, CustomerClassification.REGULAR}
            ),
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(),
        ),
        "general_inquiry": BankingPolicyRule(
            action_type="general_inquiry",
            allowed_tiers=frozenset(
                {
                    CustomerClassification.PREMIUM,
                    CustomerClassification.REGULAR,
                    CustomerClassification.NON_CUSTOMER,
                }
            ),
            requires_authentication=False,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(),
        ),
        "premium_banking": BankingPolicyRule(
            action_type="premium_banking",
            allowed_tiers=frozenset({CustomerClassification.PREMIUM}),
            requires_authentication=True,
            allow_routing_as_inquiry=True,
            prohibited_commitments=frozenset(),
        ),
    }


__all__ = ["default_banking_policy"]

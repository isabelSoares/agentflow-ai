"""Trusted healthcare information catalog and risk patterns for claim verification."""

from __future__ import annotations

from healthcare_support.domain.advanced_guardrails import (
    CoverageStatus,
    RiskPattern,
    TrustedHealthcareCatalog,
    TrustedHealthcareEntry,
)

DEFAULT_RISK_PATTERNS: tuple[RiskPattern, ...] = (
    RiskPattern(
        pattern=r"\b(guarantee\w*|guaranteed)\b",
        reason_category="unsupported_claim",
        examples=["We guarantee full coverage", "guaranteed approval"],
    ),
    RiskPattern(
        pattern=r"\b(coverage\s+amount|reimbursement\s+rate|cost\s+of)\b.*\d+",
        reason_category="unsupported_claim",
        examples=["Coverage amount is €5000", "reimbursement rate of 80%"],
    ),
    RiskPattern(
        pattern=r"\b(cost|fee\w*|charges?)\b.*\d+",
        reason_category="unsupported_claim",
        examples=["The cost is €25", "charges of 1%"],
    ),
    RiskPattern(
        pattern=r"\b(approved?|approval)\b",
        reason_category="unsupported_claim",
        examples=["Your insurance claim is approved", "approval is guaranteed"],
    ),
    RiskPattern(
        pattern=r"\b(eligible|eligibility)\b",
        reason_category="unsupported_claim",
        examples=["You are eligible for coverage", "eligibility requirements are"],
    ),
    RiskPattern(
        pattern=r"\b(claim|referral|appointment)\b.*\b(completed|sent|executed|scheduled)\b",
        reason_category="unsupported_claim",
        examples=["Your referral has been completed"],
    ),
)

DEFAULT_TRUSTED_HEALTHCARE_CATALOG = TrustedHealthcareCatalog(
    catalog_id="default",
    entries={
        "specialist_referral": TrustedHealthcareEntry(
            topic="specialist_referral",
            verified_statements=[
                "Specialist referrals are coordinated through our Insurance and Billing Department.",
                "Referral availability depends on clinical need and specialist capacity.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
        "insurance_billing": TrustedHealthcareEntry(
            topic="insurance_billing",
            verified_statements=[
                "Insurance coverage depends on the patient's plan and clinical documentation.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
        "premium_healthcare": TrustedHealthcareEntry(
            topic="premium_healthcare",
            verified_statements=[
                "Premium patients have access to dedicated patient support coordinators.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
        "general_healthcare": TrustedHealthcareEntry(
            topic="general_healthcare",
            verified_statements=[
                "We offer appointment assistance, insurance guidance, and general healthcare support.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
    },
    risk_patterns=DEFAULT_RISK_PATTERNS,
)

_CATALOG_REGISTRY: dict[str, TrustedHealthcareCatalog] = {
    "default": DEFAULT_TRUSTED_HEALTHCARE_CATALOG,
}


def get_catalog(ref: str = "default") -> TrustedHealthcareCatalog:
    """Return the trusted healthcare catalog for the given reference.

    Missing references are treated as empty catalogs so that callers never
    invent claims.
    """
    return _CATALOG_REGISTRY.get(
        ref,
        TrustedHealthcareCatalog(
            catalog_id=ref,
            entries={},
            risk_patterns=DEFAULT_RISK_PATTERNS,
        ),
    )


def register_catalog(catalog: TrustedHealthcareCatalog) -> None:
    """Register a catalog for runtime lookup."""
    _CATALOG_REGISTRY[catalog.catalog_id] = catalog

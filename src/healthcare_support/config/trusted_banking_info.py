"""Trusted banking information catalog and risk patterns for claim verification."""

from __future__ import annotations

from healthcare_support.domain.advanced_guardrails import (
    CoverageStatus,
    RiskPattern,
    TrustedBankingCatalog,
    TrustedBankingEntry,
)

DEFAULT_RISK_PATTERNS: tuple[RiskPattern, ...] = (
    RiskPattern(
        pattern=r"\b(guarantee\w*|guaranteed)\b",
        reason_category="unsupported_claim",
        examples=["We guarantee a 15% return", "guaranteed approval"],
    ),
    RiskPattern(
        pattern=r"\b(annual\s+return|interest\s+rate|rate\s+of)\b.*\d+",
        reason_category="unsupported_claim",
        examples=["Our interest rate is 5%", "annual return of 10%"],
    ),
    RiskPattern(
        pattern=r"\b(fee\w*|charges?)\b.*\d+",
        reason_category="unsupported_claim",
        examples=["The fee is €25", "charges of 1%"],
    ),
    RiskPattern(
        pattern=r"\b(approved?|approval)\b",
        reason_category="unsupported_claim",
        examples=["Your loan is approved", "approval is guaranteed"],
    ),
    RiskPattern(
        pattern=r"\b(eligible|eligibility)\b",
        reason_category="unsupported_claim",
        examples=["You are eligible for", "eligibility requirements are"],
    ),
    RiskPattern(
        pattern=r"\btransfer\b.*\b(completed|sent|executed)\b",
        reason_category="unsupported_claim",
        examples=["Your transfer has been completed"],
    ),
)

DEFAULT_TRUSTED_BANKING_CATALOG = TrustedBankingCatalog(
    catalog_id="default",
    entries={
        "yacht_insurance": TrustedBankingEntry(
            topic="yacht_insurance",
            verified_statements=[
                "Yacht insurance is available through our marine insurance specialists.",
                "Coverage depends on vessel value, navigation area, and usage.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
        "mortgage_rates": TrustedBankingEntry(
            topic="mortgage_rates",
            verified_statements=[
                "Mortgage rates vary based on term, loan-to-value ratio, and patient profile.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
        "premium_banking": TrustedBankingEntry(
            topic="premium_banking",
            verified_statements=[
                "Premium banking patients have access to dedicated relationship managers.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
        "general_banking": TrustedBankingEntry(
            topic="general_banking",
            verified_statements=[
                "We offer a range of everyday banking products and services.",
            ],
            coverage_status=CoverageStatus.PARTIAL,
        ),
    },
    risk_patterns=DEFAULT_RISK_PATTERNS,
)

_CATALOG_REGISTRY: dict[str, TrustedBankingCatalog] = {
    "default": DEFAULT_TRUSTED_BANKING_CATALOG,
}


def get_catalog(ref: str = "default") -> TrustedBankingCatalog:
    """Return the trusted banking catalog for the given reference.

    Missing references are treated as empty catalogs so that callers never
    invent claims.
    """
    return _CATALOG_REGISTRY.get(
        ref,
        TrustedBankingCatalog(
            catalog_id=ref,
            entries={},
            risk_patterns=DEFAULT_RISK_PATTERNS,
        ),
    )


def register_catalog(catalog: TrustedBankingCatalog) -> None:
    """Register a catalog for runtime lookup."""
    _CATALOG_REGISTRY[catalog.catalog_id] = catalog
